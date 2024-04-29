ML Import Wizard is a user facing Django app that takes flat square data files, or linked flat square data files, and decomposes them for importing into a Django ORM.  One of the weaknesses of an ORM is that while it does a good job turning data tables into objects, they are not great at composing objects into larger structures.  Toward this end ML Import Wizard uses introspection to observe Django models and their relationships, and uses that information to create needed Django objects from the import.

It is designed to take input data files as they are, associating fields with Django model attributes, including the ability to combine, split, and transform data in fields to fit them into the ORM.

As a user facing tool, it is designed to allow end users to manage their own data imports without having to go to the database back end or use the Admin tools.
