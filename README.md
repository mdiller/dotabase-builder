# Dotabase Builder
A collection of scripts and programs to extract dota's game files and build an sqlite database. See the output of this builder at my [Dotabase repository](https://github.com/mdiller/dotabase "Dotabase").

## VPK Extraction
The main library/tool that this builder leans on is [ValveResourceFormat](https://github.com/SteamDatabase/ValveResourceFormat "Valve Source 2 file decompiler/compiler"). This lovely project is what allows me to extract the data from dota's vpk files, and decompile some of the obscure file formats like vsnd_c into more friendly ones like mp3.

## Dota 2 Wiki Scraper
As a focus of dotabase is the extraction of the Hero Responses data, I wanted to extract the subtitles/captions for each response. Unfortunatly, these are stored in .dat files, and as of the time of this project creation, I have not found a reliable way to decompile these back into their original .txt format. Instead, I have decided to scrape this information from the [Dota 2 Wiki](http://dota2.gamepedia.com/Dota_2_Wiki "Dota 2 Wiki - Gamepedia"). A bit of a hackish method, but it works. 

## valve2json.py
Although the [ValveResourceFormat](https://github.com/SteamDatabase/ValveResourceFormat "Valve Source 2 file decompiler/compiler") decompiler does a good job of decompiling the game files into readable text files, they are still not in a format that is easily readable by programs. To that end, I convert all of the files containing information I need into .json files. I do this by doing a bunch of regex substitutions.