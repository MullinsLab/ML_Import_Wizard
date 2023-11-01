from django.conf import settings
from django.views.generic.base import View
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string

import os
import json

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard.forms import UploadFileForImportForm, NewImportSchemeForm
from ml_import_wizard.models import ImportScheme, ImportSchemeFile, ImportSchemeItem, ImportSchemeFileField
from ml_import_wizard.utils.simple import sound_user_name, resolve_true, table_resolve_key_values_to_string
from ml_import_wizard.utils.importer import importers

class ManageImports(LoginRequiredMixin, View):
    """ The starting place for importing.  Show information on imports, started imports, new import, etc. """

    def get(self, request, *args, **kwargs):
        """ Handle a get request.  Returns a starting import page. """
        importers: list[dict] = []
        user_import_schemes: list[dict] = []

        # Bring in the importers from settings
        for importer, importer_dict in settings.ML_IMPORT_WIZARD['Importers'].items():
            importer_item: dict[str] = {
                'name': importer_dict.get('long_name', importer_dict['name']),
                'importer': importer, # Used for URLs
            }

            if description := importer_dict.get("description"): importer_item["description"] = description

            importers.append(importer_item)

        # Show Import Schemes that this user owns
        for import_scheme in ImportScheme.objects.filter(user_id=request.user.id):
            user_import_scheme_item: dict = {
                'name': import_scheme.name,
                'id': import_scheme.id,
                'importer': import_scheme.importer,
                "description": import_scheme.description,
            }

            user_import_schemes.append(user_import_scheme_item)
 
        return render(request, "ml_import_wizard/manager.html", context={'importers': importers, 'user_import_schemes': user_import_schemes})


class NewImportScheme(LoginRequiredMixin, View):
    """ View for creating a new import """

    def get(self, request, *args, **kwargs):
        """ Build a new Import """
    
        importer: str = kwargs['importer_slug']
        importer_name: str = settings.ML_IMPORT_WIZARD['Importers'][importer]['name']

        return render(request, "ml_import_wizard/new_scheme.html", context={
            'form': NewImportSchemeForm(importer_slug=importer, initial={'name': f"{sound_user_name(request.user)}'s {importer_name} import"}), 
            'importer': importer_name
        })
    
    
    def post(self, request, *args, **kwargs):
        """ Save the new import """

        importer: str = kwargs["importer_slug"]
        form: form = NewImportSchemeForm(request.POST)

        if form.is_valid():
            import_scheme = ImportScheme(name=form.cleaned_data['name'], description=form.cleaned_data["description"], importer=importer, user=request.user)
            import_scheme.save()

            request.session['current_import_scheme_id'] = import_scheme.id

            return HttpResponseRedirect(reverse('ml_import_wizard:scheme', kwargs={'import_scheme_id': import_scheme.id}))
        
        else:
            # Needs to have a better error
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))


class DoImportScheme(LoginRequiredMixin, View):
    """ Do the actual import stuff """

    def get(self, request, *args, **kwargs):
        """ Do the actual import stuff """
        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))

        # Return the user to the /import page if they don't have a valid import_scheme_id to work on
        if import_scheme_id is None:
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))

        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))
        
        request.session['current_import_scheme_id'] = import_scheme_id

        actions: list = []
        # First make sure that there is one or more file to work from
        if import_scheme.files.count() == 0:
            action: dict = {
                'name': 'No data file',
                "description": "You'll need one or more files to import data from.",
                'urgent': True,
                'start_expanded': True,
            }
            actions.append(action)

        return render(request, 'ml_import_wizard/scheme.html', context={
            'importer': settings.ML_IMPORT_WIZARD['Importers'][import_scheme.importer]['name'], 
            'import_scheme': import_scheme, 
            'actions': actions}
        )
    
    
class ListImportSchemeItems(LoginRequiredMixin, View):
    """' List the ImportSchemeItems for a particular ImportScheme """

    def get(self, request, *args, **kwargs):
        """ Produce the list of ImportSchemeItems  """

        import_scheme: ImportScheme = ImportScheme.objects.get(pk=kwargs['import_scheme_id'])
        file_settings: dict = import_scheme.files_min_status_settings()
        skip_fields: bool = False

        # Initialize with a 0 for files list
        import_scheme_items: list[int|str] = [0]

        if (not import_scheme.files.count()
            or not file_settings["inspected"]
            or (import_scheme.files.count()>=2 
                and (not import_scheme.settings.get('primary_file_id', None)
                    or not import_scheme.settings.get('file_links', None)
                )
            )
        ):
            skip_fields = True

        if not skip_fields:
            # Display fields from the importer
            importer = importers[import_scheme.importer]
            
            for app in importer.apps:
                for model in app.models:
                    import_scheme_items.append(f"{app.name}-{model.name}")

        return JsonResponse({
            'import_scheme_items': import_scheme_items
        })

    
class DoImportSchemeItem(LoginRequiredMixin, View):
    """ Show and store ImportItems """

    def get(self, request, *args, **kwargs):
        """ Get information about an Import Item """

        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))
        import_item_id: int = kwargs['import_item_id']

        return_data: dict = {}

        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))
        
        if (import_item_id == 0):
            # import_item_id 0 always refers to associated files
            if import_scheme.files.count() == 0:
                return_data = {
                    'name': 'No data file',
                    "description": "You'll need one or more files to import data from.",
                    'form': render_to_string('ml_import_wizard/fragments/scheme_file.html', request=request, context={
                        'form': UploadFileForImportForm(), 
                        'path': reverse('ml_import_wizard:scheme_item', kwargs={'import_scheme_id': import_scheme.id, 'import_item_id': 0})
                    }),
                    'urgent': True,
                    'start_expanded': True,
                    "model": "ml_import_wizard_file_uploader",
                }

            else:
                files = import_scheme.files.all()

                name: str = "1 file uploaded" if import_scheme.files.count() == 1 else f"{import_scheme.files.count()} files uploaded"
                description: str = ("There is 1 file" if len(files) == 1 else f"There are {len(files)} files") + " uploaded for this import."
                form: str = ""                                          # The form part of the page
                list_bit: str = ""                                      # The list part.  Goes into description or form depending on if there is a form
                field_list: list = []                                   # List of fields in the form.  Used to check completeness
                start_expanded: bool = False                            # Start the accordion expanded
                urgent: bool = False                                    # Give the accordion a red border
                needs_form: bool = False                                # there is a form needed to collect data
                needs_linking: bool = False                             # files in the scheme haven't been linked yet
                needs_primary: bool = False                             # the scheme doesn't have a primary file yet
                hide_file_list: bool = False                            # hide the list part of the files bit
                selectpicker: bool = False                              # Triggers the selectpicker function to display bootsrtap-selects
                tooltip: bool = False                                   # Triggers tooltip decorators
                files_excluding_master: list[ImportSchemeFile] = []     # List of all the files that aren't the master
                primary_file: ImportSchemeFile = None                   # The master file
                model: str = "---setup_files---"

                # Present form if files have not been preinspected
                for file in files:
                    if file.status.preinspected == False:
                        field_list.append(f"first_row_header_{file.id}")
                        start_expanded = urgent = needs_form = True

                if not field_list:
                    # Present form if a primary file has not been selected
                    if not import_scheme.settings.get("primary_file_id"):
                        if len(files) == 1:
                            import_scheme.settings["primary_file_id"] = files[0].id
                            import_scheme.save(update_fields=["settings"])
                        else:
                            field_list.append("primary_file_id")
                            start_expanded = urgent = needs_form = needs_primary = hide_file_list = tooltip = True

                    # Present form if files have not been linked togehter, but only if everything is preinspected
                    elif not import_scheme.files_linked and file.status.preinspected:
                        for file in files:
                            if file.id == int(import_scheme.settings.get("primary_file_id")):
                                primary_file = file
                            else:
                                files_excluding_master.append(file)
                                field_list.append(f"linked-{ file.id }")
                                field_list.append(f"primary-{ file.id }")

                        start_expanded = urgent = needs_form = needs_linking = hide_file_list = selectpicker = tooltip = True

                list_bit = render_to_string('ml_import_wizard/fragments/file_list.html', request=request, context={
                        "files": import_scheme.files.all(),
                        "needs_form": needs_form,
                        "needs_linking": needs_linking,
                        "needs_primary": needs_primary,
                        "hide_file_list": hide_file_list,
                        "files_excluding_master": files_excluding_master,
                        "primary_file": primary_file,
                    })
                
                if needs_form:
                    form = list_bit
                else:
                    description += list_bit

                return_data = {
                    "name": name,
                    "description": description,
                    "start_expanded": start_expanded,
                    "urgent": urgent,
                    "form": form,
                    "fields": field_list,
                    "model": model,
                    "selectpicker": selectpicker,
                    "tooltip": tooltip,
                }
      
        return JsonResponse(return_data)


    def post(self, request, *args, **kwargs):
        """ Save or create an Import Item """
        
        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))
        import_item_id: int = kwargs['import_item_id']

        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))
        
        if (import_item_id == 0):
            #import_item_id 0 always refers to associated files

            if resolve_true(request.POST.get("---file_saved---", False)):
                check_for_inspect: list[ImportSchemeFile] = []
                
                # Dictionary for linked attributes, file: field
                linked_files: dict = {}

                for attribute, value in request.POST.items():
                    if attribute in ("csrfmiddlewaretoken", "---file_saved---"): continue

                    if "first_row_header_" in attribute:
                        import_scheme_file = ImportSchemeFile.objects.get(pk=attribute.split("_")[-1])
                        import_scheme_file.settings["first_row_header"] = value
                        import_scheme_file.save(update_fields=["settings"])

                        check_for_inspect.append(import_scheme_file)

                    if "primary_file_id" in attribute:
                        import_scheme.settings["primary_file_id"] = value
                        import_scheme.save(update_fields=["settings"])

                    if "linked-" in attribute:
                        file_id = int(attribute.split("-")[-1])
                        linked_files[file_id] = {
                            "child": int(value.replace("**field**", "")), 
                            "primary": int(request.POST.get(f"primary-{file_id}", "").replace("**field**", ""))
                        }

                if linked_files:
                    import_scheme.settings["file_links"] = linked_files
                    import_scheme.save(update_fields=["settings"])
                
                # Check to see if any files that have been altered are ready to inspect
                for import_scheme_file in check_for_inspect:
                    if import_scheme_file.ready_to_inspect:
                        import_scheme_file.set_status_by_name("Preinspected")
                        import_scheme_file.save(update_fields=["status"])
                        os.popen(os.path.join(settings.BASE_DIR, 'manage.py inspect_file ') + str(import_scheme_file.id))

                return JsonResponse({'saved': True})
            else:
                form: form = UploadFileForImportForm(request.POST, request.FILES)
                # file: file = request.FILES['file']

                if form.is_valid():
                    for file in request.FILES.values():
                        import_file = ImportSchemeFile(name=file.name, import_scheme=import_scheme)
                        import_file.save()
                        with open(settings.ML_IMPORT_WIZARD["Working_Files_Dir"] + import_file.file_name, 'wb+') as destination:
                            for chunk in file.chunks():
                                destination.write(chunk)

                        import_file.set_status_by_name('Uploaded')
                        import_file.save(update_fields=["status"])
                        
                        os.popen(os.path.join(settings.BASE_DIR, 'manage.py inspect_file ') + str(import_file.id))
                    
                    return JsonResponse({'saved': True})
                else:
                    return JsonResponse({'saved': False})
            

class DoImporterModel(LoginRequiredMixin, View):
    """ Show and store Models for imort """

    def get(self, request, *args, **kwargs):
        """ Get information about a Model for import """

        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))
        app, model = kwargs['model_name'].split("-")

        return_data: dict = {}
        urgent: bool = True
        start_expanded: bool = True
        
        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))

        model_object = importers[import_scheme.importer].apps_by_name[app].models_by_name[model]
        
        field_values: dict[str: list] = {}                                      # Allowable values for fields
        field_list: list[str] = []                                              # List of fields for the javascript to itterate through
        field_strategies: dict[str: any] = {}                                   # List of field strategies to fill the form from
        show_files: bool = True if import_scheme.files.count() > 1 else False   # Supress file name in selector if there is only one file
        is_key_value_model: bool = False                                        # Indicates that this model is a key_value_model
        key_value_model_keys = []                                               # Get the default values for key_value models
        key_value_model_setup = []                                              # Object to set up the initial table

        # Stuff for key_value models
        if model_object.settings.get("key_value_model"):
            is_key_value_model = True

            key_field = model_object.settings["key_field"]
            
            keys_from_db = [getattr(object, key_field) for object in model_object.model.objects.order_by(key_field).distinct(key_field)]
            key_value_model_keys = list(set(sorted(keys_from_db + model_object.settings.get("initial_values", []))))

            try:
                import_item: ImportSchemeItem = import_scheme.items.get(app=app, model=model, field="**key_value**")
            except:
                import_item = None
            
            if import_item:
                urgent = False
                start_expanded = False

                field_strategies = import_item.strategy

                for setting, value in import_item.settings.items():
                    file_field: ImportSchemeFileField = ImportSchemeFileField.objects.get(pk=value.get("key"))
                    key_value_model_setup.append({"name": file_field.name, "key": setting, "id": value.get("key")})


        # Stuff for standard models
        else:
            # fill field_values
            for field in model_object.settings.get("load_value_fields", []):
                field_values[field] = model_object.model.objects.values_list(field, flat=True)

            # fill field_list and field_stragegies
            for field in model_object.shown_fields:
                field_list.append(f"{model_object.name}__-__{field.name}")

                items = import_scheme.items.filter(app=app, model=model, field=field.name)
                if items.count() == 0:
                    continue
                
                item = items[0]

                field_strategies[field.name] = item.settings
                field_strategies[field.name]["strategy"] = item.strategy

            # if field.name in field_strategies: 
            if field_strategies:
                urgent = False
                start_expanded = False
            else: 
                urgent = True
                start_expanded = True
            
        return_data = {
            'name': model_object.fancy_name,
            'model': model_object.name,
            "description": '',
            "fields": field_list,
            "is_key_value_model": is_key_value_model,
            "key_value_model_keys": key_value_model_keys,
            "key_value_model_setup": key_value_model_setup,
            "urgent": urgent,
            "start_expanded": start_expanded, 

            'form': render_to_string(
                'ml_import_wizard/fragments/model.html', 
                request=request, 
                context={
                    "model": model_object, 
                    "scheme": import_scheme,
                    "field_values": field_values,
                    "app": app,
                    "strategies": field_strategies,
                    "show_files": show_files,
                },
            ),
            'tooltip': True,        # Needed to trigger tooltip
            'selectpicker': True,   # Needed to trigger the selectpicker from jquery to reformat the options
        }

        return JsonResponse(return_data)

    def post(self, request, *args, **kwargs):
        """ Store information about a Model to import """

        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))
        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))
        
        app, model = kwargs.get('model_name', '').split("-")
        fields: dict[str, dict[str, any]] = {}
            
        if request.POST.get("**is_key_value_model**"):
            field = "**key_value**"
            settings = {}

            if request.POST.get("**no_import**"):
                strategy = "No Data"

            else:
                strategy = "Key Value"

                for key, value in request.POST.items():
                    if key in ("csrfmiddlewaretoken", "**is_key_value_model**"): 
                        continue
                    
                    if "**field**" in value:
                        value = {"key": int(value.replace("**field**", ""))}
                    settings[key] = value

            import_scheme.create_or_update_item(app=app, 
                                                model= model, 
                                                field=field, 
                                                strategy=strategy, 
                                                settings=settings)

        else:
            for attribute, value in request.POST.items():
                if attribute == 'csrfmiddlewaretoken': continue

                # Get the value if it's a list, and rename our field to not include the []
                if attribute[-2:] == "[]":
                    value = request.POST.getlist(attribute)
                    attribute = attribute[0:-2]
                    
                field, attribute = attribute.split(":", 1)
                if field in fields: fields[field][attribute] = value 
                else: fields[field] = {attribute: value}

            for field, values in fields.items():
                strategy: str = ''
                settings: dict = {}
                value: str = values["file_field"]

                if value == "**raw_text**":
                    strategy = "Raw Text"
                    settings["raw_text"] = values["file_field_raw_text"]

                elif value == "**select_first**":
                    strategy = "Select First"
                    settings["first_keys"] = []

                    for file_field in [f"file_field_first_{count}" for count in [1, 2, 3]]:
                        if values[file_field]:
                            settings["first_keys"].append(int(values[file_field].split("**field**")[1]))

                elif value == "**split_field**":
                    strategy = "Split Field"
                    
                    settings["split_key"] = int(values['file_field_split'].split("**field**")[1])
                    settings["splitter"] = values["file_field_split_splitter"]
                    settings["splitter_position"] = int(values["file_field_split_position"])

                elif "**field**" in value:
                    strategy = "File Field"
                    settings["key"] = int(values['file_field'].split("**field**")[1])

                elif value == "**no_data**":
                    strategy = "No Data"
                
                elif value.startswith("resolver:"):
                    resolver: str = value.split(":")[-1]

                    strategy = "Resolver"

                    settings["resolver"] = resolver
                    settings["arguments"]: list = {}

                    for argument, argument_value in [(argument.split(":")[-1], argument_value) for argument, argument_value in values.items() if argument.startswith(value)]:
                        argument_object: dict = {
                            "key": int(argument_value.split("**field**")[1]),
                        }

                        settings["arguments"][argument.split("-")[-1]] = argument_object

                else:
                    strategy = "Table Row"
                    settings["row"] = values['file_field']

                import_scheme.create_or_update_item(app=app, 
                                                    model= model, 
                                                    field=field, 
                                                    strategy=strategy, 
                                                    settings=settings)
        
        return_data = {'saved': True,}

        return JsonResponse(return_data)
    

class PreviewImportScheme(LoginRequiredMixin, View):
    """ Preview the import with data """

    def get(self, request, *args, **kwargs):
        """ Show the data """

        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))
        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))

        table = import_scheme.preview_data_table(limit_count=5)
        
        columns = json.dumps([{'field': column["name"], 'title': column["name"]} for column in table["columns"]])
        rows = json.dumps(table_resolve_key_values_to_string(table=table["rows"]))

        return render(request, "ml_import_wizard/scheme_preview.html", context={"columns": columns, "rows": rows})
    
class DescribeImportScheme(LoginRequiredMixin, View):
    """ Describe the import in an easy to digest and copy out format """

    def get(self, request, *args, **kwargs):
        """ Show the description """

        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))
        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))
        
        description = import_scheme.description_object()

        return render(request, "ml_import_wizard/scheme_description.html", context={"description": description})