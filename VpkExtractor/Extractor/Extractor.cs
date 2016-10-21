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
        public static string vpk_destination = "C:\\xampp\\htdocs\\dota-vpk"; // I am lazy but this should be read from a config file or passed in thru console args
		public static Package package;
        public static Progress progress = new Progress();
        public static int entryProgress = 0;
        public static int entryCount = 0;

        static void Main(string[] args)
        {
            package = new Package();
            package.Read("C:\\Program Files (x86)\\Steam\\steamapps\\common\\dota 2 beta\\game\\dota\\pak01_dir.vpk");

            Logger.Start();

            try
            {
                ExtractFiles("vsnd_c", true);
                ExtractFiles("png");
                ExtractFiles("txt");
            }
            catch (Exception e)
            {
                Console.WriteLine("stopped because: " + e.Message);
            }

            Console.WriteLine("\ndone!\n{0}", Logger.Report);
            Logger.DumpLog();
            Console.ReadKey(); // Wait for key to close
        }
		

		/// <summary>
		/// Extracts all files with the indicated extension from the vpk folder to the destination folder
		/// </summary>
		/// <param name="extension">The extension/filetype to extract</param>
		/// <param name="convert">Whether or not the file should be converted when extracting</param>
		private static void ExtractFiles(string extension, bool convert = false)
		{
            var entries = package.Entries[extension];

            Console.WriteLine("extracting {1} '{0}' files", extension, entries.Count);

            progress.Start(entries.Count, 5);

            foreach (var entry in entries)
            {
                EntryFile file = new EntryFile(entry, convert);
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
