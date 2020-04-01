import pandas as pd


x = dict(
    index = 100,
    name='xx'
)

data = [
    {'index': 1, 'name':'man', 'age': 100},
    {'index': 2, 'name':'man1', 'age': 10},
    {'index': 3, 'name':'man2', 'age': 50},
]

df = pd.DataFrame(data)
print(df.columns.values.tolist())
df.set_index(['index'], inplace=True)
print(df.columns.values.tolist())
print(df)

