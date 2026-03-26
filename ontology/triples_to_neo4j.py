import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class TriplesToNeo4j:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        with self.driver.session() as session:
            # Create constraints for unique IDs
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
            print("Constraints created.")

    def ingest_tbox(self, schema_file="ontology/ind_schema.json"):
        if not os.path.exists(schema_file):
            print(f"TBox file {schema_file} not found.")
            return

        with open(schema_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            schema = data.get("ontology", {})

        def process_classes(classes, parent_id=None):
            with self.driver.session() as session:
                for cls in classes:
                    # Case 1: cls is a string (leaf subclass)
                    if isinstance(cls, str):
                        cls_id = cls
                        cls_desc = ""
                        subclasses = []
                    # Case 2: cls is a dict
                    else:
                        cls_id = cls.get("id")
                        cls_desc = cls.get("description", "")
                        subclasses = cls.get("subclasses", [])

                    if not cls_id: continue

                    # Create Class node
                    session.run("""
                        MERGE (c:Class {id: $id})
                        SET c.name = $id,
                            c.description = $description
                    """, id=cls_id, description=cls_desc)
                    print(f"  Class created: {cls_id}")

                    # Create SUBCLASS_OF relationship
                    if parent_id:
                        session.run("""
                            MATCH (child:Class {id: $c_id}), (parent:Class {id: $p_id})
                            MERGE (child)-[:SUBCLASS_OF]->(parent)
                        """, c_id=cls_id, p_id=parent_id)

                    # Recurse
                    if subclasses:
                        process_classes(subclasses, parent_id=cls_id)

        print("Ingesting TBox classes...")
        process_classes(schema.get("classes", []))
        print("TBox ingestion complete.")

    def ingest_abox(self, triples_file="ontology/extracted_triples.json"):
        if not os.path.exists(triples_file):
            print(f"ABox file {triples_file} not found. Batch extraction might still be running.")
            return

        with open(triples_file, "r", encoding="utf-8") as f:
            triples = json.load(f)

        with self.driver.session() as session:
            count = 0
            for t in triples:
                try:
                    s = str(t.get("subject", t.get("get", ""))).strip()
                    p = str(t.get("predicate", "")).strip()
                    o = str(t.get("object", "")).strip()
                    
                    if not s or not p or not o: continue

                    # Create nodes as Entity (if not already Class)
                    session.run("MERGE (e:Entity {id: $id})", id=s)
                    session.run("MERGE (e:Entity {id: $id})", id=o)

                    # Create relationship
                    # Relationship types in Neo4j must be alphanumeric/underscore
                    rel_type = "".join(c if c.isalnum() else "_" for c in p.upper()).strip("_")
                    if not rel_type: rel_type = "RELATED_TO"

                    cypher = f"""
                    MATCH (source {{id: $source_id}}), (target {{id: $target_id}})
                    MERGE (source)-[r:{rel_type}]->(target)
                    SET r.original_predicate = $p,
                        r.source_context = $context,
                        r.source_location = $location,
                        r.source_md = $source_md
                    """
                    
                    # Ensure all params are strings to avoid CypherTypeError
                    session.run(cypher, 
                                source_id=s, 
                                target_id=o, 
                                p=p,
                                context=str(t.get("source_context", "")),
                                location=str(t.get("source_location", "")),
                                source_md=str(t.get("source_md", "")))
                    count += 1
                except Exception as e:
                    print(f"Error ingesting triple {t}: {e}")
            
            print(f"Successfully ingested {count} ABox triples.")

if __name__ == "__main__":
    ingestor = TriplesToNeo4j()
    ingestor.create_constraints()
    ingestor.ingest_tbox()
    ingestor.ingest_abox()
    ingestor.close()
