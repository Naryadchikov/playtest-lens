# Follow-ups

One list for things found but not fixed: a pre-existing review finding, a case that could happen but hasn't, an idea that would widen the scope. One line each, with where it came from. Swept before the freeze.

- The COGITO adapter logs a pickup only when the item lands in a new inventory slot (`picked_up_new_inventory_item`). A pickup that stacks onto an existing slot, and currency with `add_on_pickup`, write no line. From task 07 (Grok's report), 2026-10-27.
