import importlib

from django.conf import settings
from django.apps import apps
from django.db.models import fields, ForeignKey, Model
from django.utils.module_loading import import_string

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from weakref import proxy

from ml_import_wizard.utils.simple import fancy_name, deep_exists
from ml_import_wizard.exceptions import UnresolvedInspectionOrder


importers: dict = {}


class BaseImporter(object):
    """ Base class to inherit from """

    def __init__(self, parent: object = None, name: str = None, **settings) -> None:
        if parent: self.parent = proxy(parent)  # Use a weakref so we don't have a circular refrence, defeating garbage collection
        self.name = name
        self.settings = {}
        
        for setting, value in settings.items():
            self.settings[setting] = value
    
    def __str__(self):
        """ Return the name attribute as __str__ """
        return f"{self.__class__}: {self.name}"

    @property
    def fancy_name(self) -> str:
        return fancy_name(self.name)
    
        
class Importer(BaseImporter):
    """ Class to hold the importers from settings.ML_IMPORT_WIZARD """

    def __init__(self, *, parent: object = None, name: str = None, type: str = None, description: str = None, long_name: str = None, **settings) -> None:
        """ Initalize the object """
        super().__init__(parent, name, **settings)

        self.long_name = long_name
        self.type = type
        self.apps = []
        self.apps_by_name = {}

    def get_model_by_name(self, model_name: str=None) -> object|None:
        """ Search all apps for a model by name """
        
        if not model_name:
            return None
        
        for app in self.apps:
            if model := app.models_by_name.get(model_name):
                return model

        return None


class ImporterApp(BaseImporter):
    """ Class to hold apps to import into """

    def __init__(self, *, parent: object = None, name: str='', **settings) -> None:
        """ Initialize the object """
        super().__init__(parent, name, **settings)
        
        self.models = []
        self.models_by_name = {}
        self.models_by_import_order = []

        parent.apps.append(self)
        parent.apps_by_name[self.name] = self


class ImporterModel(BaseImporter):
    """ Holds information about a model that should be imported from files """

    def __init__(self, *, parent: object = None, name: str = None, model: object = None, **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)
        
        self.model = model      # Get the Django model so we can do queries against it
        self.fields = []
        self.fields_by_name = {}
        self.unused_fields = []

        parent.models.append(self)
        parent.models_by_name[self.name] = self

        if self.settings.get("key_value_model"):
            if "key_field" not in self.settings:
                self.settings["key_field"] = "key"
            
            if "value_field" not in self.settings:
                self.settings["value_field"] = "value"

    @property
    def foreign_key_fields(self) -> list:
        """ Returns a list of fields that refer to foreign keys """

        return [field for field in self.fields if field.is_foreign_key]
    
    @property
    def has_foreign_key(self) -> bool:
        """ Returns true if the model has one or more foreign keys """

        if self.foreign_key_fields: return True
        return False
    
    @property
    def shown_fields(self) -> list:
        """ Lists all the fields that should be shown in the importer """

        return [field for field in self.fields if not (field.is_foreign_key and "foreign_model_lookup" not in field.settings)]
    
    @property
    def is_key_value(self) -> bool:
        """ True if the model stores keys and values """

        return self.settings.get("key_value_model", False)
    
    @property
    def key_value_children(self) -> bool:
        """ List of key/value models that are pointing to this model """
        
        return [field.key_value_linked_model for field in self.fields+self.unused_fields if field.is_key_value_link]
    
    @property
    def table(self) -> str:
        """ returns the db table name to query against """

        return self.model.objects.model._meta.db_table
    

class ImporterField(BaseImporter):
    """ Holds information about a field that should be imported from files """

    def __init__(self, *, parent: object = None, name: str = None, field: object=None, **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)
        
        self.field = field      # Get the Django field so we can do queries against it
        
        if field.editable:
            parent.fields.append(self)
            parent.fields_by_name[self.name] = self
        else:
            parent.unused_fields.append(self)

        # Set up the resolver, which is a function that is used to translate user input into a value for the importer
        self.resolvers: dict = {}
        for resolver in self.settings.get("resolvers", []):
            function = import_string(resolver)

            resolver_object: dict = {
                "full_name": resolver.replace(".", "-"),
                "fancy_name": fancy_name(resolver.split(".")[-1]),
                "description": function.__doc__,
                "function": function,
                "user_input_arguments": [],
                "field_lookup_arguments": [],
            }

            for argument in function.__code__.co_varnames[0:function.__code__.co_kwonlyargcount]:
                if argument.startswith("user_input_"):
                    arg_name: str = argument.replace("user_input_", "", 1)
                    arg_object: dict = {
                        "name": arg_name,
                        "fancy_name": fancy_name(arg_name)
                    }
                    resolver_object["user_input_arguments"].append(arg_object)

                elif argument.startswith("field_lookup_"):
                    resolver_object["field_lookup_arguments"].append(argument.replace("field_lookup_", "", 1))

            self.resolvers[resolver_object["full_name"]] = resolver_object

    @property
    def is_foreign_key(self) -> bool:
        """ True if the field has a foreign key """

        return isinstance(self.field, ForeignKey)
    
    @property 
    def is_key_value_link(self) -> bool:
        """ True if this is a relationship field and it points to a key/value model """

        if self.field.related_model:
            app: str = self.field.related_model._meta.app_label
            model: str = self.field.related_model.__name__

            if model_object := self.parent.parent.parent.apps_by_name.get(app, {}).models_by_name.get(model, {}):
                return model_object.is_key_value
        
        return False

    @property
    def key_value_linked_model(self) -> object|None:
        """ Returns the model that the field is linked to or None"""

        if self.field.related_model:
            app: str = self.field.related_model._meta.app_label
            model: str = self.field.related_model.__name__

            if model_object := self.parent.parent.parent.apps_by_name.get(app, {}).models_by_name.get(model, {}):
                return model_object
        
        return None

    @property
    def not_nullable(self) -> bool:
        """ True if the field is not nullable """

        return not self.field.null
    
    @property
    def is_key_field(self) -> bool:
        """ True if the field is in a key_value model and the name of this field matches model.settings.key_field """

        if not self.parent.is_key_value or self.parent.settings.get("key_field") != self.name:
            return False

        return True
    
    @property
    def is_value_field(self) -> bool:
        """ True if the field is in a key_value model and the name of this field matches model.settings.value_field """

        if not self.parent.is_key_value or self.parent.settings.get("value_field") != self.name:
            return False

        return True
    
    # @property
    # def importer(self) -> Importer:
    #     """ Returns the importer object that this model belongs to """

    #     return self.parent.importer
    
    @property
    def foreign_model_lookup_field(self) -> str:
        """ Returns the name of the field that the foreign model lookup points to """

        if "foreign_model_lookup" not in self.settings or "select_field" not in self.settings["foreign_model_lookup"]:
            return None
        
        return self.settings["foreign_model_lookup"]["select_field"]

    def foreign_model_lookup_values(self) -> list:
        """ Returns a list of values to select from """

        lookup: dict = self.settings["foreign_model_lookup"]
        model = apps.get_model(app_label=lookup["app"], model_name=lookup["model"])

        return model.objects.values_list(lookup["select_field"], flat=True).order_by(lookup["select_field"])[:200]

    def foreign_model_lookup_instance(self, value: any) -> Model:
        """ Returns the model instance that the foreign model lookup points to """

        lookup: dict = self.settings["foreign_model_lookup"]
        model = apps.get_model(app_label=lookup["app"], model_name=lookup["model"])
        instance = model.objects.get(**{lookup["select_field"]: value})

        return instance
    

def setup_importers() -> None:
    """ Initialize the importer objects from settings """

    for importer_setting, importer_value in settings.ML_IMPORT_WIZARD["Importers"].items():
        working_importer = importers[importer_setting] = Importer(
            name = importer_setting, 
            long_name = importer_value.get('long_name', ''),
            description = importer_value.get('description', ''),
        )

        for app in importer_value.get("apps", []):
            working_app: ImporterApp = ImporterApp(parent=working_importer, name=app.get('name', ''))

            # Get settingsfor the app and save them in the object, except keys in exclude_keys
            exclude_keys: tuple = ("name", "models")
            for key in filter(lambda key: key not in exclude_keys, app.keys()):
                working_app.settings[key]=app[key]

            # Get explicit list from include_models if it exists
            models: list = []
            if app.get('include_models', []):
                models = [apps.get_model(app_label=app['name'], model_name=model) 
                          for model in app.get('include_models', [])
                          if model in [app_model.__name__ for app_model in apps.get_app_config(app['name']).get_models()]
                ]

            # Get list of models from Django if the models list is still empty, excluding models in "exclude_models"
            if not models:
                models = filter(lambda model: model.__name__ not in app.get("exclude_models", []), 
                                apps.get_app_config(app['name']).get_models()
                )

            for model_object in models:
                model: dict = {}
                if deep_exists(dictionary=app, keys=["models", model_object.__name__]):
                    model = app["models"].get(model_object.__name__, {})

                # Get settingsfor the model and save them in the object, except keys in exclude_keys
                exclude_keys: tuple = ("exclude_fields", "fields")
                model_settings: dict = {}

                if deep_exists(dictionary=app, keys=["models", model_object.__name__]):
                    model_settings: dict = {setting: value for setting, value in model.items() if setting not in exclude_keys}
                
                working_model: ImporterModel = ImporterModel(parent=working_app, name=model_object.__name__, model=model_object, **model_settings)

                for field in [field for field in model_object._meta.get_fields() if field.name not in model.get("exclude_fields", [])]:
                    exclude_keys: tuple = ()
                    field_settings: dict = {setting: value for setting, value in model.get("fields", {}).get(field.name, {}).items() if setting not in exclude_keys}
                    
                    working_field: ImporterField = ImporterField(parent=working_model, name=field.name, field=field, **field_settings)

            # Step back through the models to put them into the correct order for actual data import
            # do until we have as many models in the models_by_import_order list as in the models list
            while len(working_app.models) > len(working_app.models_by_import_order):
                model_by_import_count = len(working_app.models_by_import_order)
                
                for model_object in working_app.models:
                    if model_object in working_app.models_by_import_order:
                        continue

                    # Check to see if the model has any foreign keys
                    foreign_keys = model_object.foreign_key_fields
                    if not foreign_keys:
                        working_app.models_by_import_order.append(model_object)
                        continue
                    
                    dependancy_satisfied = True
                    for field in foreign_keys:
                        if field.field.related_model.__name__ in [model.name for model in working_app.models] and field.field.related_model.__name__ not in [model.name for model in working_app.models_by_import_order]:
                            dependancy_satisfied = False
                            continue
                    
                    if dependancy_satisfied:
                        working_app.models_by_import_order.append(model_object)
                
                # Raise an exception if we make a loop and haven't increased the number of models in models_by_import_order
                # This means we've stalled out and are not making any progress
                if model_by_import_count >= len(working_app.models_by_import_order):
                    log.debug([object.name for object in working_app.models_by_import_order])
                    raise UnresolvedInspectionOrder("Order of importing models can't be resolved.  Potential circular ForeignKeys?")

