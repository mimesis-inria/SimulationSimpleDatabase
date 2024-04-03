from typing import List, Tuple, Union, Optional

from SSD.Core.Storage.adaptive_table import AdaptiveTable
from SSD.Core.Storage.database import Database


def merge(database_files: List[str],
          new_database_file: str = 'merged',
          remove_existing: bool = False):
    """
    Merge Databases in a new Database.

    :param database_files: List of Databases files.
    :param new_database_file: Name of the new Database.
    :param remove_existing: If True, Database file with name 'new_database_name' will be overwritten.
    """

    # Load working Databases
    databases = [Database(database_name=database_name).load() for database_name in database_files]
    merged_database = Database(database_name=new_database_file).new(remove_existing=remove_existing)

    # Create Tables with their Fields
    print("\nMerging the following Databases...")
    table_type = AdaptiveTable.table_type
    for db in databases:
        db.print_architecture()
        tables = db.get_tables()
        for table in tables:
            merged_database.create_table(table_name=table)
            for field_name, field in db.get_fields(table, only_names=False).items():
                if field_name != 'id':
                    field_type = type(None) if field.__class__ not in list(table_type.values()) else \
                        list(table_type.keys())[list(table_type.values()).index(field.__class__)]
                    merged_database.create_fields(table_name=table,
                                                  fields=(field_name, field_type))

    # User confirm
    merged_database.print_architecture()
    while confirm := input("Confirm new Database architecture ? (y/n): ").lower() not in ['y', 'yes', 'n', 'no']:
        print("Cannot interpret your entry.")
    if confirm in ['n', 'no']:
        print("Aborting.")
        quit()

    # Adding data
    print("Proceeding...")
    for db in databases:
        for table_name in db.get_tables():
            for line_id in range(1, db.nb_lines(table_name=table_name) + 1):
                data = db.get_line(table_name=table_name, line_id=line_id)
                if 'id' in data:
                    del data['id']
                merged_database.add_data(table_name=table_name,
                                         data=data)
        db.close()
    merged_database.close()
    print("Merge complete.")


def rename_tables(database_file: str,
                  renamed_tables: Union[Tuple[str, str], List[Tuple[str, str]]]):
    """
    Rename Tables of the Database.

    :param database_file: Database filename.
    :param renamed_tables: Tuple or list of tuples defined as ('old_name', 'new_name').
    """

    # Load the Database
    db = Database(database_name=database_file).load()

    # Check the table names to change
    renamed_tables = [renamed_tables] if type(renamed_tables) != list else renamed_tables
    current_tables = db.get_tables()
    for (old_table_name, new_table_name) in renamed_tables:
        if old_table_name not in current_tables:
            raise ValueError(f"The Database does not contain a Table with name '{old_table_name}. "
                             f"Available Tables are {current_tables}.")

    # Renaming
    print("\nRenaming Table(s). \nProceeding...")
    for (old_table_name, new_table_name) in renamed_tables:
        db.rename_table(table_name=old_table_name,
                        new_table_name=new_table_name)
    db.print_architecture()
    db.close()
    print("Renaming done.")


def rename_fields(database_file: str,
                  table_name: str,
                  renamed_fields: Union[Tuple[str, str], List[Tuple[str, str]]]):
    """
    Rename Fields of a Table of the Database.

    :param database_file: Database filename.
    :param table_name: Name of the Table.
    :param renamed_fields: Tuple or list of tuples defined as ('old_name', 'new_name').
    """

    # Load the Database
    db = Database(database_name=database_file).load()

    # Check the fields to change
    renamed_fields = [renamed_fields] if type(renamed_fields) != list else renamed_fields
    current_fields = db.get_fields(table_name=table_name)
    for (old_field_name, new_field_name) in renamed_fields:
        if old_field_name in ['id', '_dt_']:
            raise ValueError("The following fields cannot be renamed: 'id', '_dt_'")
        elif old_field_name not in current_fields:
            raise ValueError(f"The field '{old_field_name} is not in the list of available fields: {current_fields}")

    # Renaming
    print("\nRenaming Field(s). \nProceeding...")
    for (old_field_name, new_field_name) in renamed_fields:
        db.rename_field(table_name=table_name,
                        field_name=old_field_name,
                        new_field_name=new_field_name)
    db.print_architecture()
    db.close()
    print("Renaming done.")


def remove_table(database_file: str,
                 table_names: Union[str, List[str]]):
    """
    Remove Tables of the Database.

    :param database_file: Database filename.
    :param table_names: Table(s) to remove from the Database.
    """

    # Load the Database
    db = Database(database_name=database_file).load()
    table_names = [table_names] if type(table_names) != list else table_names

    # Removing
    print("\nRemoving Table(s). \nProceeding...")
    for table_name in table_names:
        db.remove_table(table_name=table_name)
    db.print_architecture()
    db.close()
    print("Removing done.")


def remove_field(database_file: str,
                 table_name: str,
                 fields: Union[str, List[str]]):
    """
    Remove Fields of a Table of the Database.

    :param database_file: Database filename.
    :param table_name: Name of the Table.
    :param fields: Field(s) to remove from the Table.
    """

    # Load the Database
    db = Database(database_name=database_file).load()

    # Check the fields to remove
    fields = [fields] if type(fields) != list else fields
    current_fields = db.get_fields(table_name=table_name)
    for field in fields:
        if field in ['id', '_dt_']:
            raise ValueError("The following fields cannot be removed: 'id', '_dt_'")
        elif field not in current_fields:
            raise ValueError(f"The field '{field} is not in the list of available fields: {current_fields}")

    # Removing
    print("\nRemoving Filed(s). \nProceeding...")
    for field in fields:
        db.remove_field(table_name=table_name,
                        field_name=field)
    db.print_architecture()
    print("Removing done.")


def export(database_file: str,
           exporter: str,
           filename: Optional[str] = None) -> None:
    """
    Export the Database file to CSV or JSON formats.

    :param database_file: Database filename.
    :param exporter: Exporter type (either 'csv' or 'json').
    :param filename: Exported filename.
    """

    # Load the Database
    db = Database(database_name=database_file).load()

    # Export to file
    db.export(exporter=exporter,
              filename=filename if filename is not None else 'export')
