# Notes on ZooKeeper

Metadata and Coordination service for Distributed Systems
Distributed configuration service, synchronization service, and naming registry for large distributed systems
Distributed systems are a zoo. They are chaotic and hard to manage, and ZooKeeper is meant to keep them under control

## What is need for a distributed corordination service?
* In the past, each application was a single program running on a single computer with a single CPU. Today, things have changed. In the Big Data and Cloud Computing world, applications are made up of many independent programs running on an ever-changing set of computers.
* ZooKeeper was designed to be a robust service that enables application developers to focus mainly on their application logic rather than coordination. It exposes a simple API, inspired by the filesystem API, that allows developers to implement common coordination tasks, such as electing a master server, managing group membership, and managing metadata.
* Having an ensemble of servers enables ZooKeeper to tolerate faults and scale throughput.

## Philosophy of ZooKeeper
* ZooKeeper does not expose primitives directly
* Instead, it exposes a file system-like API comprised of a small set of calls that enables applications to implement their own primitives
* Typically, recipes are used to denote these implementations of primitives
* Recipes include ZooKeeper operations that manipulate small data nodes, called znodes, that are organized hierarchically as a tree, just like in a file system.
* The absence of data often conveys important information about a znode. In a master-worker example, for instance, the absence of a master znode means that no master is currently elected
* Znodes may or may not contain data. If a znode contains any data, the data is stored as a byte array

## API Overview
* create /path data: Creates a znode named with /path and containing data
* delete /path: Deletes the znode /path
* exists /path: Checks whether /path exists
* setData /path data: Sets the data of znode /path to data
* getData /path: Returns the data in /path
* getChildren /path: Returns the list of children under /path

### Notes
* One important note is that ZooKeeper does not allow partial writes or reads of the znode data. When setting the data of a znode or reading it, the content of the znode is replaced or read entirely.
* ZooKeeper clients connect to a ZooKeeper service and establish a session through which they make API calls.


### Modes
* When creating a new znode, you also need to specify a mode. The different modes determine how the znode behaves.
* Persistent and ephemeral znodes: A znode can be either persistent or ephemeral. A persistent znode /path can be deleted only through a call to delete . An ephemeral znode, in contrast, is deleted if the client that created it crashes or simply closes its connection to ZooKeeper.
* Persistent znodes are useful when the znode stores some data on behalf of an application and this data needs to be preserved even after its creator is no longer part of the system. For example, in the master-worker example, we need to maintain the assignment of tasks to workers even when the master that performed the assignment crashes.
* Ephemeral znodes convey information about some aspect of the application that must exist only while the session of its creator is valid. For example, the master znode in our master-worker example is ephemeral. Its presence implies that there is a master and the master is up and running. If the master znode remains while the master is gone, then the system won’t be able to detect the master crash. This would prevent the system from making progress, so the znode must go with the master. We also use ephemeral znodes for workers. If a worker becomes unavailable, its session expires and its znode in /workers disappears automatically.
* An ephemeral znode can be deleted in two situations:
* 1. When the session of the client creator ends, either by expiration or because it explicitly closed.
* 2. When a client, not necessarily the creator, deletes it.
* Sequential znodes: A znode can also be set to be sequential. A sequential znode is assigned a unique, mo‐ notonically increasing integer. This sequence number is appended to the path used to create the znode. For example, if a client creates a sequential znode with the path /tasks/ task- , ZooKeeper assigns a sequence number, say 1, and appends it to the path. The path of the znode becomes /tasks/task-1 . Sequential znodes provide an easy way to create znodes with unique names. They also provide a way to easily see the creation order of znodes.

### Watches and Notifications
* Because ZooKeeper is typically accessed as a remote service, accessing a znode every time a client needs to know its content would be very expensive: it would induce higher latency and more operations to a ZooKeeper installation
* Clients register with ZooKeeper to receive notifications of changes to znodes. Registering to receive a notification for a given znode consists of setting a watch. A watch is a one-shot operation, which means that it triggers one notification. To receive multiple notifications over time, the client must set a new watch upon receiving each notification.
* ZooKeeper produces different types of notifications, depending on how the watch corresponding to the notification was set. A client can set a watch for changes to the data of a znode, changes to the children of a znode, or a znode being created or deleted.
* To set a watch, we can use any of the calls in the API that read the state of ZooKeeper. These API calls give the option of passing a Watcher object or using the default watcher.

### Versions
Each znode has a version number associated with it that is incremented every time its data changes. A couple of operations in the API can be executed conditionally: setDa ta and delete . Both calls take a version as an input parameter, and the operation succeeds only if the version passed by the client matches the current version on the server.

## Architecture
ZooKeeper servers run in two modes: standalone and quorum. Standalone mode is pretty much what the term says: there is a single server, and ZooKeeper state is not replicated. In quorum mode, a group of ZooKeeper servers, which we call a ZooKeeper ensemble, replicates the state, and together they serve client requests.
ZooKeeper Quorums
In quorum mode, ZooKeeper replicates its data tree across all servers in the ensemble. But if a client had to wait for every server to store its data before continuing, the delays might be unacceptable. In public administration, a quorum is the minimum number of legislators required to be present for a vote. In ZooKeeper, it is the minimum number of servers that have to be running and available in order for ZooKeeper to work.

### Sessions
Before executing any request against a ZooKeeper ensemble, a client must establish a session with the service. The concept of sessions is very important and quite critical for the operation of ZooKeeper. All operations a client submits to ZooKeeper are associated to a session. When a session ends for any reason, the ephemeral nodes created during that session disappear.
Sessions offer order guarantees, which means that requests in a session are executed in FIFO (first in, first out) order. Typically, a client has only a single session open, so its requests are all executed in FIFO order. If a client has multiple concurrent sessions, FIFO ordering is not necessarily preserved across the sessions.


## Getting Started
* docker search zookeeper
* docker pull jplock/zookeeper
* zk-shell

### Subcommands
#### Connect
* connect 172.17.0.2:2181
* tree
* ls
* ls zookeeper
* create <path> <value> [ephemeral] [sequence] [recursive]
* By default persistent, non sequence and non-recusive
* Create a node: create /foo 'bar'
* Create an ephemeral znode: create /foo1 '' true
* Create an ephemeral|sequential znode: create /a/b- '' true true
* Recursively create a path: create /very/long/path/here '' false false true
* get foo
* cd foo
* create node 'value'
* create node1 'value1'
* rm /foo

#### Copy
* cp file:///etc/passwd zk://localhost:2181/passwd
* get passwd
* cp zk://localhost:2181/passwd zk://othercluster:2183/mypasswd
* cp zk://localhost:2181/something json://!tmp!backup.json/ true true

Mirroring paths to between clusters or JSON files is also supported. Mirroring replaces the destination path with the content and structure of the source path.
create /source/znode1/znode11 'Hello' false false true
(CONNECTED) /> create /source/znode2 'Hello' false false true
(CONNECTED) /> create /target/znode1/znode12 'Hello' false false true
(CONNECTED) /> create /target/znode3 'Hello' false false true

mirror /source /target

#### Watch
* watch start <path> [debug] [depth]
* watch start /foo true
* create /foo/bar 'bar'
* set /foo/bar 'bar1'
* rm /foo/bar

#### Check
* check <path> <version>

#### Transactions
* txn 'create /foo "start"' 'check /foo 0' 'set /foo "end"' 'rm /foo 1'

zero <path> [version]

diff
help
pwd
txn  
add_auth
disconnect
history
quit
watch
cd
du
ifind
reconnect
zero
check
dump
igrep
rm
child_count    ephemeral_endpoint  json_cat           rmr
child_matches  exists              json_count_values  session_endpoint
child_watch    exit                json_get           session_info
chkzk          fill                json_valid         set
connect        find                loop               set_acls
cons           get                 ls                 summary
cp             get_acls            mirror             sync
create         grep                mntr               tree
