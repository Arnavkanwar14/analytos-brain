# Content Agent Output

Provider: `groq:llama-3.1-8b-instant`

## Draft Blog Post

### How does Stockly Monte Carlo safety stock work and what customer outcome supports it?

Stockly is a Pull Kanban inventory intelligence platform designed for discrete manufacturing. One of its key features is the Monte Carlo safety-stock simulation, which helps plants stop carrying excess inventory without risking stockouts. In this article, we'll delve into how Stockly Monte Carlo safety stock works and explore a customer outcome that supports its effectiveness.

#### What is Monte Carlo safety-stock simulation?

According to Stockly's Monte Carlo safety-stock simulation feature, "Runs 10,000 demand/lead-time scenarios per SKU nightly to recommend optimal safety stock instead of static min/max rules." This means that the simulation generates a large number of random demand and lead-time scenarios for each SKU, allowing Stockly to calculate the optimal safety stock levels that minimize the risk of stockouts while avoiding excess inventory.

#### How does Stockly Monte Carlo safety stock work?

The Monte Carlo simulation is a key component of Stockly's Pull Kanban engine. Here's a high-level overview of how it works:

1. Stockly collects data on demand and lead times for each SKU.
2. The Monte Carlo simulation generates 10,000 random demand and lead-time scenarios for each SKU.
3. Stockly calculates the optimal safety stock levels for each SKU based on the simulation results.
4. The recommended safety stock levels are then used to adjust the kanban loops and replenishment signals.

#### Customer outcome supporting Stockly Monte Carlo safety stock

A Midwest precision machining pilot achieved a 21% reduction in on-hand inventory value within 90 days, with a revenue of $120M and ~3,400 active SKUs. This outcome demonstrates the effectiveness of Stockly's Monte Carlo safety-stock simulation in reducing inventory levels while minimizing the risk of stockouts.

### Sources

* `stockly-monte-carlo-safety-stock`: Monte Carlo safety-stock simulation feature description
* `stockly-inventory-value-reduction`: Customer outcome supporting Stockly Monte Carlo safety stock
* `stockly`: Stockly product overview
* `stockly-product-overview.md`: Source document for Stockly product overview
