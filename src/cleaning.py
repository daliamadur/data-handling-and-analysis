import pandas as pd
import numpy as np
import re
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

pd.set_option('future.no_silent_downcasting', True)

#load
def load_csv(path:str):
    try:
        with open(path, "r", encoding="utf-8") as csv_file:
            return pd.read_csv(csv_file)
    except Exception as e:
        print(e)

COLUMNS_TO_KEEP = [
    "Name",
    "Manufacturer",
    "Type",
    "Home", 
    "Hybrid",
    "Handheld",
    "Generation",
    "Release date",
    "Discontinued",
    "Units sold",
    "Media_Type",
    "Launch price_GBP"
]

MEDIA = {
    "In-built": ["printed circuit board", "inbuilt chip", "built in"],
    "Cartridge": ["cartridge", "hucard", "game pak", "datacard", "mmc", "game card"],
    "Optical Disc": ["cd-rom", "gd-rom", "disc", "cd", "dvd", "blu-ray"],
    "Digital Distribution": ["digital distribution"]
}

#main: pd.DataFrame = load_csv("..//data//main df.csv")
#working_table = load_csv("..//data//raw//Fifth_generation_of_video_game_consoles-2.csv")
main_table = load_csv("..//data//main df.csv")

#clean
def split_lines(ml_list: str):
    split_pos = [0]
    
    for match in re.finditer(r"[a-zA-Z][A-Z][a-z]", ml_list):
        split_pos.append(match.span()[0] + 1)

    split_pos.append(len(ml_list))

    string_arr = [ml_list[split_pos[i]:split_pos[i+1]] for i in range(len(split_pos) - 1)]

    return string_arr
    
def get_eu_release(release_dates: str):
    #ADD MORE DATE PATTERNS - year only, date month + year, month + year
       
    eu_release_date = re.search(r"[A-Z]*\/{,1}EU\/{,1}[A-Z]*: [a-zA-Z]+ [0-9]{,2}, [0-9]{4}", release_dates)
    release = eu_release_date if eu_release_date else re.search(r"WW: [a-zA-Z]+ [0-9]{,2}, [0-9]{4}", release_dates)

    return release.group().split()[-1] if release else None #release year :3

def get_release_price(release_price: str):
    if release_price:
        if "equivalent" in release_price:
            price_in_2020s = re.search(r"(equivalent to £[0-9,]+ in [0-9]{4})", release_price) #.split()[2]
            price = price_in_2020s.group().split()[2]
            
            return float(re.sub(",", "", price[1:])) #release price with inflation + without symbol
        else:
            if release_price.startswith("£"):
                return float(release_price[1:])
            else:
                return float(release_price) if release_price.isnumeric() else np.nan
    else:
        return None

def get_media(media_type: str):
    primary_media = split_lines(media_type)[0].lower()

    for category, labels in MEDIA.items():
        for label in labels:
            if label in primary_media:
                return category
            
    return None

def get_discontinued_date(discontinued_date: str):
    dates = [
        r"^EU: [a-zA-Z]+ [0-9]{,2},{,1} [0-9]{4}", #european
        r"^WW: [a-zA-Z]+ [0-9]{,2},{,1} [0-9]{4}", #worlwide
        r"^[a-zA-Z]+ [0-9]{,2},{,1} [0-9]{4}", #specified
        r"^Q[0-9]{1} [0-9]{4}" #unspecified
    ]

    for date in dates:
        match = re.match(date, discontinued_date)
        if match:
            return re.search(r"[0-9]{4}", match.group()).group()

def remove_whitespace(table:pd.DataFrame):
    for column in table.columns:
        if table[column].dtype == "str":
            table[column] = table[column].map(str.strip)
        else:
            pass

def clean_columns(table:pd.DataFrame):
    #check if first row are indices ? drop : keep
    index_column_count: int = 0
    total_column_count: int = 0
    generation = None
    indexed = None

    table = table.replace("", None)

    for column in table.columns:
        #check for generations column + pop
        if column == "Generation":
            generation = table.pop(column)[0]
            total_column_count -=1

        if column.isnumeric() or "Unnamed" in column:
            index_column_count+=1

        total_column_count +=1

    #🔵 remove index row
    if total_column_count == index_column_count:
        table.columns = table.iloc[0]
        indexed = True

    #🟣 remove index column
    table = table.select_dtypes(exclude=['number'])

    #🟢 normalise multi-level headings
    new_head = []

    #extract first and second
    first_row = table.iloc[0].values
    second_row = table.iloc[1].values

    #first column (name/console) will be the same if multi-level
    if first_row[0] in second_row[0]:
        for i, head in enumerate(first_row):                
            #add heading to new headings if duplicate
            if str(head) in str(second_row[i]):
                new_head.append(head)
            else:
                #add heading + subheading concat to new headings
                new_head.append(f"{head}_{second_row[i]}")

        #drop sub row
        table = table.drop([0, 1]).reset_index(drop=True)
    
    #🔴 leave single-level headings unchanged
    elif indexed:
        new_head = list(table.columns)
        table = table.drop(0).reset_index(drop=True)
    else:
        new_head = list(table.columns)
        

    #normalise column titles
    for i, column in enumerate(new_head):
        match column:
            case "Release dates":
                new_head[i] = "Release date"
            case "Console" | "System":
                new_head[i] = "Name"
            case "Launch prices_GBP":
                new_head[i] = "Launch price_GBP"
            case "Media_Game media":
                new_head[i] = "Media_Type"

    #rename columns
    table.columns = new_head
    
    if generation:
        table["Generation"] = generation

    #drop columns that won't be used in final dataset
    table = table.drop(columns=[col for col in table.columns if col not in COLUMNS_TO_KEEP])

    return table

def clean_rows(table:pd.DataFrame):
    #handle missing values
    table = table.replace(np.nan, None)

    #remove citations
    table = table.replace(r"\[[0-9a-zA-Z]+\]", "", regex=True)

    #strip whitespace
    #remove_whitespace(table)

    #extract useful vales
    if "Manufacturer" in table.columns:
        table["Manufacturer"] = table["Manufacturer"].map(lambda x: re.match(r"^[a-zA-Z]+", x).group())
    
    #release date
    if "Release date" in table.columns:
        table["Release date"] = table["Release date"].map(lambda x: get_eu_release(x))
    
    #launch price
    if "Launch price_GBP" in table.columns:
        table["Launch price_GBP"] = table["Launch price_GBP"].map(lambda x: get_release_price(x))

    #media type
    if "Media_Type" in table.columns:
        table["Media_Type"] = table["Media_Type"].map(lambda x: get_media(x))

    #discontinued
    if "Discontinued" in table.columns:
        table["Discontinued"] = table["Discontinued"].map(lambda x: get_discontinued_date(x))
    
    #remove extra text
    table = table.replace(r"\([0-9a-zA-Z\s,.]+\)", "", regex=True).infer_objects(copy=False)

    #remove nan values
    table = table.replace(np.nan, None)

    #convert column datatypes - types in notion
    
    return table

#testing
def test():
    test_val = 10
    for path in Path("..//data//raw//by_generation").iterdir():
        #path = "..//data//raw//by_generation//Eighth_generation_of_video_game_consoles-2.csv"

        working_table = load_csv(path)
        print(path.stem)

        #inspect
        cleaned_cols = clean_columns(working_table)
        cleaned_rows = clean_rows(cleaned_cols)

        console = Console()
        #console.print(Markdown(cleaned_cols.to_markdown()))
        console.print(Markdown(cleaned_rows.to_markdown()))
        print("-" * 50)

        test_val -= 1

        if test_val == 0:
            break

test()