import pandas as pd
import geopandas as gpd


PATH = r"Fallzahlen&HZ 2014-2023.xlsx"
GEO_PATH = r"bezirksgrenzen.geojson"

BEZIRKE = ["Mitte", "Friedrichshain-Kreuzberg", "Pankow", "Charlottenburg-Wilmersdorf", "Spandau", "Steglitz-Zehlendorf", "Tempelhof-Schöneberg", "Neukölln", "Treptow-Köpenick", "Marzahn-Hellersdorf", "Lichtenberg", "Reinickendorf"]
STRAFTATEN = ["Bezeichnung (Bezirksregion)", "Straftaten \n-insgesamt-", "Raub", "Straßenraub,\nHandtaschen-raub", "Körper-verletzungen \n-insgesamt-", "Gefährl. und schwere Körper-verletzung", "Freiheits-beraubung, Nötigung,\nBedrohung, Nachstellung", "Diebstahl \n-insgesamt-"]

NEW_COLUMN_NAMES = {
    "Straftaten \n-insgesamt-": "Gesamt",
    "Raub": "Raub",
    "Straßenraub,\nHandtaschen-raub": "Straßenraub",
    "Körper-verletzungen \n-insgesamt-": "Körperverletzung",
    "Gefährl. und schwere Körper-verletzung": "schwere Körperverletzung",
    "Freiheits-beraubung, Nötigung,\nBedrohung, Nachstellung": "Freiheitsberaubung",
    "Diebstahl \n-insgesamt-": "Diebstahl",
    "Bezeichnung (Bezirksregion)": "Gemeinde_name"
}

COLUMNS_TO_SUBTRACT = ["Raub", "Körperverletzung", "schwere Körperverletzung", "Freiheitsberaubung", "Diebstahl"]


def load_and_filter_data(year, path=PATH):
    """Loads data for a specific year, filters by relevant columns and districts."""
    sheet_name = f"Fallzahlen_{year}"
    df = pd.read_excel(path, sheet_name=sheet_name, skiprows=4)
    df_filtered = df[df["Bezeichnung (Bezirksregion)"].isin(BEZIRKE)][STRAFTATEN]
    df_filtered["Jahr"] = year
    return df_filtered.rename(columns=NEW_COLUMN_NAMES)


def calculate_other_crimes(df):
    """Calculates the 'Other' crime category by subtracting known categories from the total."""
    df["Other"] = df["Gesamt"] - df[COLUMNS_TO_SUBTRACT].sum(axis=1)
    return df


def merge_with_geo_data(df, geo_path=GEO_PATH):
    """Merges crime data with GeoJSON data, handles missing districts."""
    df_geo = gpd.read_file(geo_path)
    merged_df = df.merge(df_geo, on="Gemeinde_name", how="inner")
    merged_df = merged_df.drop(columns=["gml_id", "Gemeinde_schluessel", "Land_name", "Land_schluessel", "Schluessel_gesamt"])
    return gpd.GeoDataFrame(merged_df, geometry='geometry')


def load_and_process_crime_data():
    """Loads, processes, and returns the crime data."""
    all_data = [load_and_filter_data(year) for year in range(2014, 2024)]
    df_combined = pd.concat(all_data, ignore_index=True)
    df_combined = calculate_other_crimes(df_combined)
    return merge_with_geo_data(df_combined)


if __name__ == "__main__":
    crime_data = load_and_process_crime_data()
    print(crime_data.head())  # Print the first 5 rows of the resulting GeoDataFrame
