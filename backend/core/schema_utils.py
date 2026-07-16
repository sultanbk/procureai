# backend/core/schema_utils.py
# Helper utility to clean Pydantic/JSON schemas for Vertex AI SDK.

def clean_vertex_schema(schema):
    if not isinstance(schema, dict):
        return schema
        
    def dereference_schema(s: dict) -> dict:
        def resolve_refs(node, defs):
            if isinstance(node, dict):
                if '$ref' in node:
                    ref_path = node['$ref']
                    ref_name = ref_path.split('/')[-1]
                    ref_node = defs.get(ref_name, {})
                    resolved = resolve_refs(ref_node, defs)
                    new_node = {k: v for k, v in node.items() if k != '$ref'}
                    new_node.update(resolved)
                    return new_node
                else:
                    return {k: resolve_refs(v, defs) for k, v in node.items()}
            elif isinstance(node, list):
                return [resolve_refs(item, defs) for item in node]
            return node

        defs = s.get('$defs', {})
        cleaned_schema = resolve_refs(s, defs)
        if '$defs' in cleaned_schema:
            del cleaned_schema['$defs']
        return cleaned_schema

    def clean_schema_for_vertex(node):
        if isinstance(node, dict):
            if 'anyOf' in node:
                non_null = [s for s in node['anyOf'] if isinstance(s, dict) and s.get('type') != 'null']
                if non_null:
                    merged = {k: v for k, v in node.items() if k != 'anyOf'}
                    merged.update(non_null[0])
                    return clean_schema_for_vertex(merged)
                else:
                    node = {"type": "string"}

            ALLOWED_KEYS = {'type', 'format', 'description', 'nullable', 'enum', 'items', 'properties', 'required'}
            cleaned = {}
            for k, v in node.items():
                if k in ALLOWED_KEYS:
                    if k == 'type' and isinstance(v, str):
                        mapping = {
                            "string": "STRING",
                            "integer": "INTEGER",
                            "number": "NUMBER",
                            "boolean": "BOOLEAN",
                            "array": "ARRAY",
                            "object": "OBJECT"
                        }
                        cleaned[k] = mapping.get(v.lower(), v.upper())
                    elif k == 'properties':
                        cleaned[k] = {pk: clean_schema_for_vertex(pv) for pk, pv in v.items()}
                    elif k == 'items':
                        cleaned[k] = clean_schema_for_vertex(v)
                    else:
                        cleaned[k] = v
            return cleaned
        elif isinstance(node, list):
            return [clean_schema_for_vertex(item) for item in node]
        return node

    return clean_schema_for_vertex(dereference_schema(schema))
