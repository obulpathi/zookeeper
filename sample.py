from kazoo import client

HOST="172.17.0.2"
PORT="2181"


zk = client.KazooClient(hosts=HOST+":"+PORT)
zk.start()

# Ensure a path, create if necessary
zk.ensure_path("/my/favorite")

# Create a node with data
zk.create("/node", "value")

if zk.exists("/node"):
    print "node exists"
else:
    print "Does not exist"
