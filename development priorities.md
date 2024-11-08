# Development Priorities

## Database

* Get data for database internals - webscraping initiated

* Identify database content

* Load database content

## Protobuf Specification

* templated, may need tweaks in the future

## REST Server

* workerInit api definition (combined with workerInit service)

* workerChar api call (combined with workerChar service)

* workerRoll api call (combined with workerRoll service)

* workerLookup api call (combined with workerLookup service)

REST needs to:

* send/receive calls via REST and protobufs to/from Discord Bot

* send/receive protobufs to Redis or RabbitMQ message queues

## Message Queueing (e.g. REDIS or RabbitMQ)

* Do we need to have RAFT or similar for consensus on scaling?

* Set up to receive and relay protobuf messages between

    * Discord and REST

    * REST and Workers

* 8 queues

    * REST to 

        * workerInit

        * workerRoll

        * workerChar

        * workerLookup

    * Cassandra Database service to 

        * workerInit

        * workerRoll

        * workerChar

        * workerLookup

## Discord API and Bot

* Protobuf + Discord Bot + Messaging to REST server

* Is the point-of-implementation for the command tree

    * take in and parse the arguments of a command

    * pump args into the appropriate protobuf message

    * send protobuf message to REST

## Docker / Kubernetes images

* templated

* will need code implemented to build

* need to fine-tune the workers - I favor small / lightweight workers with autoscaling (horizontal)

## Webscraping / Data Gathering

* How do I prioritize what to pull?

* Do we only want weapons and spells for now?

* What about the lookup service?  what all do we want to offer for lookup?