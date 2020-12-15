### Site availability monitoring and reporting

The current service written in Python is used for the periodic site 
availability monitoring. 
It consists of two main parts:
- Producer: Periodically checks sites based on rules from yaml config and 
sends the results as events to some *event bus*.
- Consumer: Consumes the events from event bus and writes data to some 
*persistent storage*.
- Schema Registry: is a simple local in-memory schema registry based on
 Pydantic model shared between consumer and producer for messages validation.


The event bus used by producer and consumer and persistent storage are 
pluggable interfaces, but currently `Apache Kafka` and `PostgreSQL` used for 
these purposes. 


### Checker rules
Check the `producer/sites.yaml` as an example of rules you can set for 
the checker.

### Configuration
Because the service uses Kafka and Postgres they must be configured.
It can be done by setting values on `example.env` and then running services
via Docker-Compose.

Also to securely connect to Kafka you need to provide 
`.pem`, `.cert` and `.key` files. You can put them in `configs` folder and 
then specify a path to them in `example.env` file.


### How to run
For running docker-compose is used with `consumer` and `producer` services.
- Run producer: `make run-producer`
- Run consumer: `make run-consumer`
- Run both: `make run`
- Run all tests: `make test`

### Next Steps
- Integration tests with running Apache Kafka and PostgreSQL
- Using Apache Avro for messages schema validation for producer and consumer
- The operations done here are mostly I/O heavy so in case we need to monitor 
much more sites:
    - Producer: Use async apscheduler, async Kafka client and async HTTP Client
    to run everything in asyncio event loop
    - Consumer: Use async Kafka client and async PostgreSQL compatible 
    library for writes.
- Different DockerFiles, split requirements and separate projects 
for producer and consumer.
- HTTP API and simple UI to retrieve monitoring results from PostgreSQL.
 