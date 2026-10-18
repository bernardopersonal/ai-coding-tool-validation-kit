# Design notes

`calc.stats` holds pure functions without side effects. Inputs are sequences of
numbers; an empty sequence raises `ValueError`. Functions must not modify their
input. The median of an even number of values is the mean of the two middle
values.
