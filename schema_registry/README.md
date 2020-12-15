# Simple local Schema registry

Currently this schema_registry is just a simple package for registering 
Pydantic models that support validation for specific topics. This is a toy
implementation and works because consumer and producer co-exist 
in the same project. 

Ideally both producer and consumer should be using Apache Avro schemas and 
separate schema registry storage for messages validation.  
