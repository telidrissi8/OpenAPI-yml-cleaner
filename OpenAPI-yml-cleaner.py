import yaml
import re
import copy
import json

opendoc_yaml_file = './openapi.yml'
cleaned_opendoc = 'cleaned_opendoc.yaml'

# Load the opendoc YAML file
with open(opendoc_yaml_file, 'r') as file:
    opendoc_data = yaml.safe_load(file)

##############################################################

# List of HTTP routes (with methods) to keep
routes_to_keep = [
    {'path': '/path1', 'method': 'get'},
    {'path': '/path1', 'method': 'get'},
]

# Identify and remove unused routes
routes_to_remove = []
for path, path_data in list(opendoc_data.get('paths', {}).items()):
    for method, method_data in list(path_data.items()):
        if {'path': path, 'method': method} not in routes_to_keep:
            routes_to_remove.append((path, method))

# Remove the identified routes
for path, method in routes_to_remove:
    del opendoc_data['paths'][path][method]

# Remove empty path entries
empty_paths = [path for path, path_data in opendoc_data.get('paths', {}).items() if not path_data]
for path in empty_paths:
    del opendoc_data['paths'][path]

##############################################################

opendoc_copy_data = copy.deepcopy(opendoc_data)
if 'components' in opendoc_copy_data and 'schemas' in opendoc_copy_data['components']:
    del opendoc_copy_data['components']['schemas']

with open(cleaned_opendoc, 'w') as file:
    yaml.dump(opendoc_copy_data, file, default_flow_style=False)

with open(cleaned_opendoc, 'r') as file:
    opendoc_data_raw_without_shemas = file.read()

# Use re.findall to find all matches in the opendoc YAML text
pattern = r'#/components/schemas/(\w+)'
referenced_schema_names = set(re.findall(pattern, opendoc_data_raw_without_shemas))

kept_schemas = {}

# Collect referenced schemas names
for schema_name in referenced_schema_names:
    kept_schemas[schema_name] = opendoc_data['components']['schemas'][schema_name]

def traverse_and_retain_schemas(schema_definition, kept_schemas):
    schema_string = json.dumps(schema_definition)
    schema_names_from_schema_definition = set(re.findall(pattern, schema_string))
    for schema_name in schema_names_from_schema_definition:
        if schema_name not in kept_schemas:
            kept_schemas[schema_name] = schema_definition
            ref_schema = opendoc_data['components']['schemas'].get(schema_name)
            traverse_and_retain_schemas(ref_schema, kept_schemas)

# Collect schemas needed from other schemas (recursively)
kept_schemas_copy = copy.deepcopy(kept_schemas)
for schema_name, schema_definition in kept_schemas_copy.items():
    traverse_and_retain_schemas(schema_definition, kept_schemas)

# Update the 'components' section with the filtered schema components
opendoc_data['components']['schemas'] = kept_schemas

##############################################################

# Initialize a list to store the values
tag_values = set()

for path, path_data in opendoc_data.get('paths', {}).items():
    for method, method_data in path_data.items():
        if "tags" in method_data:
            tag_values.update(method_data["tags"])
            
opendoc_data['tags'] = [{'name': tag, 'description': ''} for tag in tag_values]

##############################################################

# TODO : rearange order of section
# TODO : replace localhost

# Save the cleaned opendoc YAML file
with open(cleaned_opendoc, 'w') as file:
    yaml.dump(opendoc_data, file, default_flow_style=False)
