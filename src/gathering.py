import pandas as pd
import requests, time
from rich.console import Console
from pathlib import Path

HTML_PATH = "..//data//raw_html_pages"
MD_PATH = "..//data//md_for_inspection"

console = Console()

# load in each source
# 🕹️ VIDEO GAME CONSOLES BY GENERATION
GENERATIONS = {"First": 1,
               "Second": 2,
               "Third": 3,
               "Fourth": 4,
               "Fifth": 5,
               "Sixth": 6,
               "Seventh": 7,
               "Eighth": 8,
               "Ninth": 9
               }
GEN_URL = 'https://en.wikipedia.org/wiki/{}_generation_of_video_game_consoles'

# 🪙 BEST SELLING VIDEO GAMES
BEST_SELLING_CONSOLES_URL = 'https://en.wikipedia.org/wiki/List_of_best-selling_game_consoles'

# 🗺️ BEST SELLING VIDEO GAMES BY REGION
BEST_SELLING_BY_REGION_URL = 'https://en.wikipedia.org/wiki/List_of_best-selling_game_consoles_by_region'

URLS = [GEN_URL.format(gen) for gen in GENERATIONS.keys()]
URLS.extend([BEST_SELLING_BY_REGION_URL, BEST_SELLING_CONSOLES_URL])

# manual source
# ✏️ PREDECESSOR + SUCCESSOR MAPPING -> nintnedo, playstation, xbox, sega etc.
SUCCESSOR_MAP = {}

def load_and_save_html(url: str):
    #user agent headers for bot policy :3
    HEADERS = {'User-Agent': 'ConsoleDataAnalysisBotUwU/1.0 (portfolio project)'}

    rq = requests.get(url, headers=HEADERS)
    path = f"{HTML_PATH}//{url.split("/")[-1]}.html"

    print(rq.text, file=open(path, "w", encoding="utf-8"))

    return path

def save_all_sources(sources: list[str]):
    for url in sources:
        with console.status("Inspecting tables"):
            time.sleep(5)
            try:
                name = url.split("/")[-1]
                load_and_save_html(url)

                console.log(f"{name}.html loaded ✅")
                
            except Exception as e:
                print(f"Error with {name}: {e}")

#generate md to look at table (easier than looking at the terminal)
def inspect_tables(title: str, tables: list[pd.DataFrame], md_path: str):
    with open(f"{md_path}//{title}.md", "w", encoding="utf-8") as f:
        f.write("# Contents\n")
        for i in range(len(tables)):
            f.write(f"- [Table {i}](#table-{i})\n")
        for i, table in enumerate(tables):
            f.write(f"# Table {i}\n")
            f.write("[Back to top](#contents)\n")
            f.write(table.to_markdown())
            f.write(f"\n---\n")

#iteratively go through all html pages and create md files for them :3
def inspect_all_sources(html_dir:str, md_dir:str):
    for html_path in Path(html_dir).iterdir():
        with console.status("Inspecting tables"):
            try:
                with open(html_path, "r", encoding="utf-8") as html_page:
                    tables = pd.read_html(html_page)
                    inspect_tables(html_path.stem, tables, md_dir)

                    console.log(f"{html_path.stem}.md created for inspection ✅")
            except Exception as e:
                print(e)
                break

#get names of all files to ensure correct indexing
for path in Path(HTML_PATH).iterdir():
    print(path.stem)

REGIONS = [
    "asia",
    "japan",
    "china",
    "middle-east",
    "south-korea",
    "americas",
    "north-america",
    "canada",
    "mexico",
    "united-states",
    "brazil",
    "europe",
    "western-europe",
    "france",
    "germany",
    "spain",
    "united-kingdom",
    "australia",
    "south-africa",
    "other-unknown"
]

#GET CORRECT TABLES FROM FILES
TABLES_MAP = {
    "Eighth_generation_of_video_game_consoles": "1.T, 2.T, 4.T",
    "Fifth_generation_of_video_game_consoles": "1.T, 2.T, 3, 4.T, 6.T",
    "First_generation_of_video_game_consoles": "1.T, 2.T, 4.T",
    "Fourth_generation_of_video_game_consoles": "1.T, 2.T, 3, 4.T, 6.T",
    "List_of_best-selling_game_consoles": [0],
    "List_of_best-selling_game_consoles_by_region": [i for i, _ in enumerate(REGIONS)],
    "Ninth_generation_of_video_game_consoles": "1.T, 3.T",
    "Second_generation_of_video_game_consoles": "1.T, 2.T, 3, 4.T, 5.T, 7.T",
    "Seventh_generation_of_video_game_consoles": "1.T, 2.T, 3.T, 6.T",
    "Sixth_generation_of_video_game_consoles": "1.T, 2, 3.T, 4, 6.T",
    "Third_generation_of_video_game_consoles": "1.T, 2, 4.T"
}

def save_dataframes_to_file(html_dir: str, dataframe_dir:str, index_map:dict):
    #load html from file
    for html_path in Path(html_dir).iterdir():

        #get correct table indices for the correct file
        indices = index_map.get(html_path.stem)
        
        #add console generation number to table if applicable, and correct index formatting
        if "generation" in html_path.stem:
            generation = GENERATIONS.get(html_path.stem.split("_")[0])
            indices = indices.replace(" ", "").split(",")

        with console.status(f"Saving raw tables {indices} from {html_path.stem}"):
            try:
                #open html page and read tables
                with open(html_path, "r", encoding="utf-8") as html_page:
                    tables = pd.read_html(html_page)
                    
                    #get indices of correct tables from dict 
                    for table_index in indices:
                        #get index and whether table should be transposed
                        #"1" -> table 1 + no transpose, "1.T" -> table 1 + transpose FOR STRINGS
                        index = int(table_index[0]) if type(table_index) == str else table_index
                        transpose = "T" in table_index if type(table_index) == str else False

                        dataframe = tables[index]

                        #transpose comparison tables to get attributes as columns
                        if transpose:
                            dataframe = dataframe.T
                        
                        #add generation column for less cleaning overhead
                        if generation:
                            dataframe["Generation"] = generation

                        #get table stem -> region if region else index
                        #List_of_best-selling_game_consoles_by_region-europe
                        #Eighth_generation_of_video_game_consoles-4
                        table = REGIONS[index] if "region" in html_path.stem else index

                        #save dataframes to file for cleaning + analysis :3
                        with open(f"{dataframe_dir}//{html_path.stem}-{table}.csv", "w", encoding="utf=8") as f:
                            f.write(dataframe.to_csv())

                        console.log(f"{dataframe_dir}//{html_path.stem}-{table}.csv saved for cleaning ✅")
                    
            except Exception as e:
                print(e)
                break

def main():
    save_all_sources(URLS)
    inspect_all_sources(HTML_PATH, MD_PATH)
    save_dataframes_to_file(HTML_PATH, "..//data//raw", TABLES_MAP)