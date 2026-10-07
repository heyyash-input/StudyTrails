# Python loops

A for loop visits each item in an iterable such as a list, string, or range.
Use indentation to mark the loop body.

```python
total = 0
for number in [2, 4, 6]:
    total += number
print(total)  # 12
```

range(3) produces 0, 1, 2. The stop value is excluded.
range(1, 4) produces 1, 2, 3.
range(0, 6, 2) produces 0, 2, 4.

break exits the innermost loop. continue skips the rest of the current
iteration and moves to the next iteration.

A while loop repeats while its condition is true. Update the relevant
state so the condition can eventually become false.

```python
count = 3
while count > 0:
    print(count)
    count -= 1
```

Practise: sum a list, count even numbers, and print a multiplication table.
