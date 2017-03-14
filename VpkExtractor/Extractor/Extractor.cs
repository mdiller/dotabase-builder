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
    public static class Extractor
    {
        public static bool log_console = true;
        public static string vpk_destination = "C:\\Development\\Projects\\dotabase-web\\dota-vpk"; // I am lazy but this should be read from a config file or passed in thru console args
        public static string dota_path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\dota 2 beta";
        public static Package package;
        public static Progress progress = new Progress();
        public static int entryProgress = 0;
        public static int entryCount = 0;

        static void Main(string[] args)
        {
            package = new Package();
            package.Read(dota_path + "\\game\\dota\\pak01_dir.vpk");

            Logger.Start();

            try
            {
                CopyNormalFile("/game/dota/resource/dota_english.txt", "/resource/dota_english.txt");
                ExtractFiles("vxml_c", true);
                ExtractFiles("vjs_c", true);
                ExtractFiles("vcss_c", true);
                ExtractFiles("png");
                ExtractFiles("txt");
                ExtractFiles("cfg");
                ExtractFiles("res");
                ExtractFiles("vsnd_c", true);
                ExtractFiles("vtex_c", true);
            }
            catch (Exception e)
            {
                Console.WriteLine("stopped because: " + e.Message);
            }

            Console.WriteLine("\ndone!\n{0}", Logger.Report);
            Logger.DumpLog();
            Console.ReadKey(); // Wait for key to close
        }

        private static void CopyNormalFile(string source, string destination)
        {
            string source_path =dota_path + source;
            string destination_path = vpk_destination + destination;

            if(!File.Exists(destination_path) || File.GetLastWriteTime(source_path) > File.GetLastWriteTime(destination_path))
            {
                // Write all data to file
                File.Copy(source_path, destination_path, true);
                if (log_console)
                {
                    Console.WriteLine("Copied file to: " + destination);
                }
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

            Console.WriteLine("extracting {1} '{0}' files", extension, entries.Count);

            progress.Start(entries.Count);

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
            Console.WriteLine("done extracting '{0}' files.", extension);
            Console.WriteLine("Status so far: {0}", Logger.Report);
        }
    }
}
