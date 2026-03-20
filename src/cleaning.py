import pandas as pd
from typing import Sequence

#load
def load_csv(path:str):
    try:
        with open(path, "r", encoding="utf-8") as csv_file:
            return pd.read_csv(csv_file)
    except Exception as e:
        print(e)

#main: pd.DataFrame = load_csv("..//data//main df.csv")
df = load_csv("..//data//raw//Fifth_generation_of_video_game_consoles-1.csv")

#inspect
print(df.columns)

#clean
def clean_columns(table:pd.DataFrame):
    #check if first row are indices ? drop : keep
    index_column_count: int = 0
    generation = None

    for column in table.columns:
        #check for generations column
        if column == "Generation":
            generation = table.pop(column)[0]

        if column.isnumeric():
            index_column_count+=1

    if len(table.columns) - index_column_count < 2:
        table.columns = table.iloc[0]

    #check if (new) second row contains first row ? (mark as multi-level) -> combine differing headings then drop
    #for 
    first_row = table.iloc[0].values
    second_row = table.iloc[1].values

    new_head = []
    similarity_count = 0
    
    for i, head in enumerate(first_row):
        if head in second_row[i]:
            new_head.append(head)
            similarity_count += 1
        else:
            new_head.append(f"{head}_{second_row[i]}")
    
    #drop first 2 rows if second row is a sub-column (over half by estimate) otherwise only drop first row
    table = table.drop(index=[0, 1]) if similarity_count > len(table.columns)/2 else table.drop(index=0)
    table.columns = new_head
    
    if generation:
        table["Generation"] = generation

    return table

#testing
clean_columns(df)
df.drop(columns=[])