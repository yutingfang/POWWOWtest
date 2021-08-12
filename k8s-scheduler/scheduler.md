# Scheduling in Kubernetes

**Scheduling** in kubernetes refers to selecting a node where a pod can be placed.

## Default scheduling

A simple overview of what the k8s scheduler does

**Node Selection**
1. Find all nodes that exist and are available in the cluster
2. Filter out unsuitable nodes (based on resource needs of the deployment, other filters) **(Predicates)**
3. Assign priority scores to each remaining node in the pool **(Priorities)**
4. select node with the highest score 

**Pod Scheduling** 
1. Pick a pod from the queue
2. Go to **Node Selection**
3. if no suitable node found, evaluate pod priority
4. Based on pod priority and type either evict an exist lower priority pod or place pod back in queue

## User-defined scheduling

A node can be specified by the user explicitly in the following ways:

### 1. nodeName

specified in the YAML definition of the resource


```yml
apiVersion: v1
kind: Pod

spec:
  containers:
  - name: manual-node
    image: my-image
  nodeName: node-name

```

In the above case the deployment is specified to happen on node "node-name"

    Pros: 
    - easy node specification
    - reproducible
    - user controlled deployment

    Cons:
    - deployment fails if specified node is unavailable/not up to required specifications of the pod
    - pod will not be able to leverage features available to typical k8s deployments

---

### 2. nodeSelector

a more flexible specification dependent on node labels and predicates

```yml
---

spec:
  containers:
  - name: abc
    image: xyz
  nodeSelector:
    # place our pod only on a node which has an SSD storage available
    disktype: ssd
    # make sure node not part of a group with given role
    role NotIn monitoring

```

    Pros:
    - more flexible
    - easy definition of nodes with known/suitable configuration 

    Cons:
    - limited to node labels

---

### 3. Affinity/Anti-affinity

expands on the expressiveness of the nodeSelector specifier. Makes the node more (affinity) or less (attractive) for scheduling.

2 modes of setting:
 - Hard/Strict -> **requiredDuringSchedulingIgnoredDuringExecution**  
    - node specifications have to be met for scheduling otherwise node will not be selected
    - meeting node specifications is the top most priority of scheduler
  
  
 - Soft/Easy -> **preferredDuringSchedulingIgnoredDuringExecution**   
    - checks for given conditions and if no nodes meets them then the scheduler will still end up selecting the next best option
    - making sure pod is deployed on a node is the top most priority
    
**Hard Affinity**

```yaml
---
spec:
 affinity:
   nodeAffinity:
     requiredDuringSchedulingIgnoredDuringExecution:
       nodeSelectorTerms:
       # functionally similar to above nodeSelector
       - matchExpressions:
         - key: feature
           operator: In
           values:
           - ssd
 containers:

---
```

**Soft Affinity**

```yaml
---
spec:
 affinity:
   nodeAffinity:
     preferredDuringSchedulingIgnoredDuringExecution:
       nodeSelectorTerms:
       # functionally similar to above nodeSelector
       - matchExpressions:
         - key: feature
           operator: In
           values:
           - ssd
 containers:

---
```

**Anti-affinity**

Use inverted predicate operators for achieving anti-affinity (NotIn, DoesNotExist, etc.)

Notes: [from official k8s documentation]

 - If you specify both nodeSelector and nodeAffinity, both must be satisfied for the pod to be scheduled onto a candidate node.
 - If you specify multiple nodeSelectorTerms associated with nodeAffinity types, then the pod can be scheduled onto a node if one of the nodeSelectorTerms can be satisfied.
 - If you specify multiple matchExpressions associated with nodeSelectorTerms, then the pod can be scheduled onto a node only if all matchExpressions is satisfied.
 - If you remove or change the label of the node where the pod is scheduled, the pod won't be removed. In other words, the affinity selection works only at the time of scheduling the pod.


**Inter-Pod Affinity/Anti-Affinity** [From k8s official documentation]

constrain which nodes your pod is eligible to be scheduled based on labels on pods that are already running on the node rather than based on labels on nodes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-pod-affinity
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: security
            operator: In
            values:
            - S1
        topologyKey: topology.kubernetes.io/zone
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: security
              operator: In
              values:
              - S2
          topologyKey: topology.kubernetes.io/zone
  containers:
  - name: with-pod-affinity
    image: k8s.gcr.io/pause:2.0
```

    Pros:
    - finer control over scheduling dependent on previous pod placement
  
    Cons:
    -  Inter-pod affinity and anti-affinity require substantial amount of processing which can slow down scheduling in large clusters significantly
    -  Pod anti-affinity requires nodes to be consistently labelled, in other words every node in the cluster must have an appropriate label matching topologyKey. If some or all nodes are missing the specified topologyKey label, it can lead to unintended behavior.

---

### 4. Scheduler scoring weightage [from k8s official documentation]

User can define custom weights to specific scores which are calculated for each suitable node by the scheduler at the time of node priority decision making

```yaml
### definition above
preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: another-node-label-key
            operator: In
            values:
            - another-node-label-value
### continued resource definition
```

The **weight** field in preferredDuringSchedulingIgnoredDuringExecution is in the range 1-100. For each node that meets all of the scheduling requirements (resource request, RequiredDuringScheduling affinity expressions, etc.), the scheduler will compute a sum by iterating through the elements of this field and adding "weight" to the sum if the node matches the corresponding MatchExpressions. This score is then combined with the scores of other priority functions for the node. The node(s) with the highest total score are the most preferred.

---

### 5. Taints and tolerations

Taints allow the user to define scheduling contraints on the nodes instead of pods.

A taint placed on a node will repel a pod. A tainted node is excluded from pod scheduling.

```
kubectl taint nodes mon01 role=monitoring:NoSchedule
```

A toleration defined in a pod will allow pod to be scheduled on a tainted node. Tainted nodes will be filtered by the scheduler unless the pod has a toleration for it. A toleration will allow a tainted node to remain in the pool of possible nodes which the scheduler can select.

```yaml
tolerations:
- key: "role"
  operator: "Equal"
  value: "monitoring"
  effect: "NoSchedule"
```
---

### 6. Pod Priority 

[https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/]

Priority indicates the importance of a Pod relative to other Pods. If a Pod cannot be scheduled, the scheduler tries to preempt (evict) lower priority Pods to make scheduling of the pending Pod possible.

Types of PriorityClasses:
 - **preempting** - can evict lower priority pods
 - **non-preempting** -  cannot preempt other pods. will stay in the scheduling queue, until sufficient resources are free, and it can be scheduled

---

## Scheduling Limitations in Kubernetes

- No resource awareness. The scheduler makes no distinction between the type of resource which needs to be scheduled. Likely that containers with specific workloads have specific resource requirements and scheduling constraints
- Limited isolation of resources by the scheduler causes interference - containers on a shared node vying for limited resources

---

## Alternative Scheduler Strategies and Related Work on Kubernetes Scheduling

### Apache Mesos: Dominant resource fairness

Ghodsi, A.; Zaharia, M.; Hindman, B.; Konwinski, A.; Shenker, S.; Stoica, I. Dominant resource fairness: Fair allocation of multiple
resource types. In Proceedings of the NSDI 2011, Boston, MA, USA, 30 March–1 April 2011.

---

### Balanced-CPU-Disk-IO-Priority dynamic scheduling algorithm (BCDI) and Balanced-Disk-IO-Priority dynamic scheduling algorithm (BCDI)

Li, D.; Wei, Y.; Zeng, B. A Dynamic I/O Sensing Scheduling Scheme in Kubernetes. In Proceedings of the 2020 4th International
Conference on High Performance Compilation, Computing and Communications, Guangzhou, China, 27–29 June 2020

Kubernetes scheduler does not take the disk I/O load of nodes into account, which leads two problems: 
1. Multiple I/O-intensive applications may be dispatched to the same node, which cause I/O bottlenecks. 
2. Pods are less likely to be scheduled on node with idle I/O and insufficient CPU, resulting in the waste of the node's I/O resource

---

### Network-aware Resource Provisioning in Kubernetes

J. Santos, T. Wauters, B. Volckaert and F. De Turck, "Towards Network-Aware Resource Provisioning in Kubernetes for Fog Computing Applications," 2019 IEEE Conference on Network Softwarization (NetSoft), 2019, pp. 351-359, doi: 10.1109/NETSOFT.2019.8806671.

---

### RL based dynamic resource provisioning

F. Bahrpeyma, H. Haghighi, and A. Zakerolhosseini, “An adaptive rl
based approach for dynamic resource provisioning in cloud virtualized
data centers,” Computing, vol. 97, no. 12, pp. 1209–1234, 2015.

---

### Progress based container scheduling for short-lived applications

    Problem definition:

    The present commercial systems, however, fail to take existing jobs on the worker into account. Although the running jobs could reflect indirectly by the resource usage on a particular worker, the expected completion time, especially for short-living computing jobs, should be taken into consideration. Assuming there is a 3-node cluster that configures to 1 manager and 2 workers. And that currrently, 3 jobs are running in this cluster, with 2 of them are being run on worker-1 and the other one being hosted by worker-2. With spread strategy, the incoming 4th job will be assigned to worker-2 to maintain an even distribution. It works perfectly fine if the existing jobs would elapse for a while after the assignment. But, if the 2 jobs on worker-1 are expected to finish in a second, the previous assignment would downgrade system performance.

Y. Fu et al., "Progress-based Container Scheduling for Short-lived Applications in a Kubernetes Cluster," 2019 IEEE International Conference on Big Data (Big Data), 2019, pp. 278-287, doi: 10.1109/BigData47090.2019.9006427.