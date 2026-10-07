# Python lists and dictionaries

A list is an ordered, mutable collection. Indexing starts at zero.
For names = ["Asha", "Ravi"], names[0] is "Asha" and names[-1] is "Ravi".
append adds one item to the end. len reports the number of items.
Slicing a list with values[start:stop] excludes the stop index.

```python
scores = [70, 80, 90]
scores.append(100)
print(scores[1:3])  # [80, 90]
```

A dictionary maps unique keys to values. Access a known key with data[key].
Use data.get(key, default) when a key may be absent.
Iterating over data.items() gives key/value pairs.

```python
student = {"name": "Asha", "score": 85}
for key, value in student.items():
    print(key, value)
```

A set stores unique elements. A tuple is an ordered, immutable sequence.
Practise: track student scores and count how often each word occurs.
