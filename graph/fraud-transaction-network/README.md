# Fraud Transaction Network Graph DB Lab

A separate lab for storing and exploring fraud transaction network data in a graph database.

This lab will reuse the account-to-account transaction data previously prepared for GAT/GATv2 fraud detection experiments.

## Goal

Model financial transaction data as a graph and explore relationships and transaction paths directly in a graph database.

```text
(Account)-[TRANSFERRED_TO]->(Account)
```

## Data Model

### Node: Account

- account identifier
- fraud label
- degree
- community
- other account-level graph features when useful

### Edge: Transaction

- source account
- destination account
- amount
- timestamp
- other transaction-level attributes when useful

## Lab Tasks

- [ ] Select and set up a graph database for the lab
- [ ] Prepare a manageable sample from the fraud transaction dataset
- [ ] Create Account nodes
- [ ] Create Transaction edges
- [ ] Store fraud labels
- [ ] Store amount and timestamp attributes
- [ ] Add degree / community attributes where useful
- [ ] Explore direct neighbors of an account
- [ ] Explore multi-hop transaction paths
- [ ] Explore neighborhoods around fraud-labeled accounts
- [ ] Compare graph exploration results with the existing GAT experiment structure

## Example Questions

- Which accounts are directly connected to a fraud-labeled account?
- Which accounts are reachable within 2-3 hops?
- What transaction paths connect two accounts?
- Are fraud-labeled accounts concentrated in particular communities?
- Are there repeated transaction patterns within a connected account group?

## Relationship to Vector Search

Graph DB and Vector DB solve different problems.

- **Graph DB**: relationship and path exploration — "How are these accounts connected?"
- **Vector DB / pgvector**: similarity search — "Which accounts or embeddings are most similar?"

A future extension can connect both approaches:

```text
Transaction Data
      ↓
   Graph DB
      ↓
Graph Exploration
      ↓
   GAT/GATv2
      ↓
Node Embeddings
      ↓
   pgvector
      ↓
Similarity Search
```

This lab is intentionally separate from the main AI-Native DBRE phases and will be implemented after the current pgvector/vector-search exercises.
