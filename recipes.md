# ZooKeeper Recipies

Out of the Box Applications: Name Service, Configuration, Group Membership
Name service and configuration are two of the primary applications of ZooKeeper. These two functions are provided directly by the ZooKeeper API.

Another function directly provided by ZooKeeper is group membership. The group is represented by a node. Members of the group create ephemeral nodes under the group node. Nodes of the members that fail abnormally will be removed automatically when ZooKeeper detects the failure.



Barriers
Distributed systems use barriers to block processing of a set of nodes until a condition is met at which time all the nodes are allowed to proceed. Barriers are implemented in ZooKeeper by designating a barrier node. The barrier is in place if the barrier node exists. Here's the pseudo code:

Client calls the ZooKeeper API's exists() function on the barrier node, with watch set to true.
If exists() returns false, the barrier is gone and the client proceeds
Else, if exists() returns true, the clients wait for a watch event from ZooKeeper for the barrier node.
When the watch event is triggered, the client reissues the exists( ) call, again waiting until the barrier node is removed.

Double Barriers
Double barriers enable clients to synchronize the beginning and the end of a computation. When enough processes have joined the barrier, processes start their computation and leave the barrier once they have finished. This recipe shows how to use a ZooKeeper node as a barrier.

The pseudo code in this recipe represents the barrier node as b. Every client process p registers with the barrier node on entry and unregisters when it is ready to leave. A node registers with the barrier node via the Enter procedure below, it waits until x client process register before proceeding with the computation. (The x here is up to you to determine for your system.)

Enter	Leave
Create a name n = b+“/”+p
Set watch: exists(b + ‘‘/ready’’, true)
Create child: create( n, EPHEMERAL)
L = getChildren(b, false)
if fewer children in L than x, wait for watch event
else create(b + ‘‘/ready’’, REGULAR)
L = getChildren(b, false)
if no children, exit
if p is only process node in L, delete(n) and exit
if p is the lowest process node in L, wait on highest process node in L
else delete(n) if still exists and wait on lowest process node in L
goto 1
On entering, all processes watch on a ready node and create an ephemeral node as a child of the barrier node. Each process but the last enters the barrier and waits for the ready node to appear at line 5. The process that creates the xth node, the last process, will see x nodes in the list of children and create the ready node, waking up the other processes. Note that waiting processes wake up only when it is time to exit, so waiting is efficient.

On exit, you can't use a flag such as ready because you are watching for process nodes to go away. By using ephemeral nodes, processes that fail after the barrier has been entered do not prevent correct processes from finishing. When processes are ready to leave, they need to delete their process nodes and wait for all other processes to do the same.

Processes exit when there are no process nodes left as children of b. However, as an efficiency, you can use the lowest process node as the ready flag. All other processes that are ready to exit watch for the lowest existing process node to go away, and the owner of the lowest process watches for any other process node (picking the highest for simplicity) to go away. This means that only a single process wakes up on each node deletion except for the last node, which wakes up everyone when it is removed.


Queues
Distributed queues are a common data structure. To implement a distributed queue in ZooKeeper, first designate a znode to hold the queue, the queue node. The distributed clients put something into the queue by calling create() with a pathname ending in "queue-", with the sequence and ephemeral flags in the create() call set to true. Because the sequence flag is set, the new pathnames will have the form _path-to-queue-node_/queue-X, where X is a monotonic increasing number. A client that wants to be removed from the queue calls ZooKeeper's getChildren( ) function, with watch set to true on the queue node, and begins processing nodes with the lowest number. The client does not need to issue another getChildren( ) until it exhausts the list obtained from the first getChildren( ) call. If there are are no children in the queue node, the reader waits for a watch notification to check the queue again.

Note
There now exists a Queue implementation in ZooKeeper recipes directory. This is distributed with the release -- src/recipes/queue directory of the release artifact.

Priority Queues
To implement a priority queue, you need only make two simple changes to the generic queue recipe . First, to add to a queue, the pathname ends with "queue-YY" where YY is the priority of the element with lower numbers representing higher priority (just like UNIX). Second, when removing from the queue, a client uses an up-to-date children list meaning that the client will invalidate previously obtained children lists if a watch notification triggers for the queue node.

Locks
Fully distributed locks that are globally synchronous, meaning at any snapshot in time no two clients think they hold the same lock. These can be implemented using ZooKeeeper. As with priority queues, first define a lock node.

Note
There now exists a Lock implementation in ZooKeeper recipes directory. This is distributed with the release -- src/recipes/lock directory of the release artifact.

Clients wishing to obtain a lock do the following:

Call create( ) with a pathname of "_locknode_/guid-lock-" and the sequence and ephemeral flags set. The guid is needed in case the create() result is missed. See the note below.
Call getChildren( ) on the lock node without setting the watch flag (this is important to avoid the herd effect).
If the pathname created in step 1 has the lowest sequence number suffix, the client has the lock and the client exits the protocol.
The client calls exists( ) with the watch flag set on the path in the lock directory with the next lowest sequence number.
if exists( ) returns false, go to step 2. Otherwise, wait for a notification for the pathname from the previous step before going to step 2.
The unlock protocol is very simple: clients wishing to release a lock simply delete the node they created in step 1.

Here are a few things to notice:

The removal of a node will only cause one client to wake up since each node is watched by exactly one client. In this way, you avoid the herd effect.
There is no polling or timeouts.
Because of the way you implement locking, it is easy to see the amount of lock contention, break locks, debug locking problems, etc.
Recoverable Errors and the GUID


If a recoverable error occurs calling create() the client should call getChildren() and check for a node containing the guid used in the path name. This handles the case (noted above) of the create() succeeding on the server but the server crashing before returning the name of the new node.
Shared Locks
You can implement shared locks by with a few changes to the lock protocol:

Obtaining a read lock:	Obtaining a write lock:
Call create( ) to create a node with pathname "guid-/read-". This is the lock node use later in the protocol. Make sure to set both the sequence and ephemeral flags.
Call getChildren( ) on the lock node without setting the watch flag - this is important, as it avoids the herd effect.
If there are no children with a pathname starting with "write-" and having a lower sequence number than the node created in step 1, the client has the lock and can exit the protocol.
Otherwise, call exists( ), with watch flag, set on the node in lock directory with pathname staring with "write-" having the next lowest sequence number.
If exists( ) returns false, goto step 2.
Otherwise, wait for a notification for the pathname from the previous step before going to step 2
Call create( ) to create a node with pathname "guid-/write-". This is the lock node spoken of later in the protocol. Make sure to set both sequence and ephemeral flags.
Call getChildren( ) on the lock node without setting the watch flag - this is important, as it avoids the herd effect.
If there are no children with a lower sequence number than the node created in step 1, the client has the lock and the client exits the protocol.
Call exists( ), with watch flag set, on the node with the pathname that has the next lowest sequence number.
If exists( ) returns false, goto step 2. Otherwise, wait for a notification for the pathname from the previous step before going to step 2.
Notes:

It might appear that this recipe creates a herd effect: when there is a large group of clients waiting for a read lock, and all getting notified more or less simultaneously when the "write-" node with the lowest sequence number is deleted. In fact. that's valid behavior: as all those waiting reader clients should be released since they have the lock. The herd effect refers to releasing a "herd" when in fact only a single or a small number of machines can proceed.
See the note for Locks on how to use the guid in the node.
Revocable Shared Locks
With minor modifications to the Shared Lock protocol, you make shared locks revocable by modifying the shared lock protocol:

In step 1, of both obtain reader and writer lock protocols, call getData( ) with watch set, immediately after the call to create( ). If the client subsequently receives notification for the node it created in step 1, it does another getData( ) on that node, with watch set and looks for the string "unlock", which signals to the client that it must release the lock. This is because, according to this shared lock protocol, you can request the client with the lock give up the lock by calling setData() on the lock node, writing "unlock" to that node.

Note that this protocol requires the lock holder to consent to releasing the lock. Such consent is important, especially if the lock holder needs to do some processing before releasing the lock. Of course you can always implement Revocable Shared Locks with Freaking Laser Beams by stipulating in your protocol that the revoker is allowed to delete the lock node if after some length of time the lock isn't deleted by the lock holder.

Two-phased Commit
A two-phase commit protocol is an algorithm that lets all clients in a distributed system agree either to commit a transaction or abort.

In ZooKeeper, you can implement a two-phased commit by having a coordinator create a transaction node, say "/app/Tx", and one child node per participating site, say "/app/Tx/s_i". When coordinator creates the child node, it leaves the content undefined. Once each site involved in the transaction receives the transaction from the coordinator, the site reads each child node and sets a watch. Each site then processes the query and votes "commit" or "abort" by writing to its respective node. Once the write completes, the other sites are notified, and as soon as all sites have all votes, they can decide either "abort" or "commit". Note that a node can decide "abort" earlier if some site votes for "abort".

An interesting aspect of this implementation is that the only role of the coordinator is to decide upon the group of sites, to create the ZooKeeper nodes, and to propagate the transaction to the corresponding sites. In fact, even propagating the transaction can be done through ZooKeeper by writing it in the transaction node.

There are two important drawbacks of the approach described above. One is the message complexity, which is O(n²). The second is the impossibility of detecting failures of sites through ephemeral nodes. To detect the failure of a site using ephemeral nodes, it is necessary that the site create the node.

To solve the first problem, you can have only the coordinator notified of changes to the transaction nodes, and then notify the sites once coordinator reaches a decision. Note that this approach is scalable, but it's is slower too, as it requires all communication to go through the coordinator.

To address the second problem, you can have the coordinator propagate the transaction to the sites, and have each site creating its own ephemeral node.

Leader Election
A simple way of doing leader election with ZooKeeper is to use the SEQUENCE|EPHEMERAL flags when creating znodes that represent "proposals" of clients. The idea is to have a znode, say "/election", such that each znode creates a child znode "/election/guid-n_" with both flags SEQUENCE|EPHEMERAL. With the sequence flag, ZooKeeper automatically appends a sequence number that is greater than any one previously appended to a child of "/election". The process that created the znode with the smallest appended sequence number is the leader.

That's not all, though. It is important to watch for failures of the leader, so that a new client arises as the new leader in the case the current leader fails. A trivial solution is to have all application processes watching upon the current smallest znode, and checking if they are the new leader when the smallest znode goes away (note that the smallest znode will go away if the leader fails because the node is ephemeral). But this causes a herd effect: upon of failure of the current leader, all other processes receive a notification, and execute getChildren on "/election" to obtain the current list of children of "/election". If the number of clients is large, it causes a spike on the number of operations that ZooKeeper servers have to process. To avoid the herd effect, it is sufficient to watch for the next znode down on the sequence of znodes. If a client receives a notification that the znode it is watching is gone, then it becomes the new leader in the case that there is no smaller znode. Note that this avoids the herd effect by not having all clients watching the same znode.

Here's the pseudo code:

Let ELECTION be a path of choice of the application. To volunteer to be a leader:

Create znode z with path "ELECTION/guid-n_" with both SEQUENCE and EPHEMERAL flags;
Let C be the children of "ELECTION", and i be the sequence number of z;
Watch for changes on "ELECTION/guid-n_j", where j is the largest sequence number such that j < i and n_j is a znode in C;
Upon receiving a notification of znode deletion:

Let C be the new set of children of ELECTION;
If z is the smallest node in C, then execute leader procedure;
Otherwise, watch for changes on "ELECTION/guid-n_j", where j is the largest sequence number such that j < i and n_j is a znode in C;
