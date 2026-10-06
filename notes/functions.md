# Python functions

Define a function with def. Parameters are input names. Arguments are the
values supplied when the function is called. return sends a value to the caller.

```python
def add(left, right):
    return left + right


answer = add(2, 3)  # 5
```

print displays text; it does not replace return. A function that reaches
its end without returning a value returns None.

Local variables normally belong to the function call that created them.
Default parameters allow an argument to be omitted.

```python
def greet(name="learner"):
    return f"Hello, {name}"
```

Avoid mutable default arguments such as an empty list. Use None and create
a new list inside the function when needed.

Practise: write functions to calculate an average, check even numbers,
and count words. For an average, explicitly reject an empty input list.
