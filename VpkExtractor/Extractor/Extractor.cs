using Newtonsoft.Json;
using SteamDatabase.ValvePak;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ValveResourceFormat;
using ValveResourceFormat.ResourceTypes;

namespace VpkExtractor
{
	public class Config
	{
		public string vpk_path { get; set; }
		public string dota_path { get; set; }

		public static Config LoadConfig(string path)
		{
			return JsonConvert.DeserializeObject<Config>(File.ReadAllText(path));
		}
	}

	public static class Extractor
	{
		public static bool log_console = false;
		public static Package package;
		public static Progress progress = new Progress();
		public static int entryProgress = 0;
		public static int entryCount = 0;
		public static Config config;

		static void Main(string[] args)
		{
			try
			{
				config = Config.LoadConfig("config.json");
			}
			catch(Exception e)
			{
				Console.WriteLine("Error loading config file");
				return;
			}

			package = new Package();
			package.Read(config.dota_path + "\\game\\dota\\pak01_dir.vpk");

			Logger.Start();

			try
			{
                CopyNormalFiles("txt");
				ExtractFiles("txt");
				ExtractFiles("vxml_c", true);
				ExtractFiles("vjs_c", true);
				ExtractFiles("vcss_c", true);
				ExtractFiles("png");
				ExtractFiles("cfg");
				ExtractFiles("res");
				ExtractFiles("vsnd_c", true);
				ExtractFiles("vtex_c", true);
			}
			catch (Exception e)
			{
                Console.WriteLine();
				Console.WriteLine("stopped because: " + e.Message);
			}

			Console.WriteLine("\ndone!\n{0}", Logger.Report);
			Logger.DumpLog();
			Console.ReadKey(); // Wait for key to close
		}

		private static void CopyNormalFile(string path)
		{
			string source_path = config.dota_path + "/game/dota" + path;
			string destination_path = config.vpk_path + path;

            if (!File.Exists(destination_path) || File.GetLastWriteTime(source_path) > File.GetLastWriteTime(destination_path))
			{
                if (!File.Exists(destination_path))
                {
                    Logger.LogNewFile(destination_path);
                }
                else
                {
                    Logger.LogOverwriteFile(destination_path);
                }
                // Write all data to file
                Directory.CreateDirectory(Path.GetDirectoryName(destination_path));
                File.Copy(source_path, destination_path, true);
			}
		}

        private static void CopyNormalFiles(string extension)
        {
            string root_path = config.dota_path + "/game/dota";

            string[] fileEntries = Directory.GetFiles(root_path, "*." + extension, SearchOption.AllDirectories);

            progress.Start(extension, fileEntries.Count());

            foreach (string filename in fileEntries)
            {
                progress.Inc();
                CopyNormalFile(filename.Replace(root_path, ""));
            }
        }
		

		/// <summary>
		/// Extracts all files with the indicated extension from the vpk folder to the destination folder
		/// </summary>
		/// <param name="extension">The extension/filetype to extract</param>
		/// <param name="convert">Whether or not the file should be converted when extracting</param>
		private static void ExtractFiles(string extension, bool convert = false, string newExtension = null)
		{
			var entries = package.Entries[extension];

			// Console.WriteLine("extracting {1} '{0}' files", extension, entries.Count);

			progress.Start(extension, entries.Count);

			foreach (var entry in entries)
			{
				EntryFile file = new EntryFile(entry, newExtension, convert);
				file.Dump();
				if(Console.KeyAvailable)
				{
					switch(Console.ReadKey(true).Key)
					{
						case ConsoleKey.Escape:
							throw new Exception("ESC pressed");
						case ConsoleKey.P:
						case ConsoleKey.Enter:
							progress.Print();
							break;
						default:
							break;
					}
				}
				progress.Inc();
			}
			// Console.WriteLine("done extracting '{0}' files.", extension);
			Console.WriteLine("Status: {0}", Logger.Report);
		}
	}
}
