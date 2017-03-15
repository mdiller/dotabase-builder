using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace VpkExtractor
{
	public static class Logger
	{
		const string log_dir = "log";
		public static List<string> newFiles = new List<string>();
		public static List<string> overwrittenFiles = new List<string>();
		public static Stopwatch timer = new Stopwatch();

		public static string Report
		{
			get { return string.Format("{0} files created, and {1} files overwritten.\nTime: {2}", newFiles.Count, overwrittenFiles.Count, timer.Elapsed); }
		}

		public static void LogNewFile(string filename)
		{
			newFiles.Add(filename);
			if (Extractor.log_console)
				Console.WriteLine("new file: " + filename);
		}

		public static void LogOverwriteFile(string filename)
		{
			overwrittenFiles.Add(filename);
			if (Extractor.log_console)
				Console.WriteLine("overwrote: " + filename);
		}

		public static void Start()
		{
			newFiles = new List<string>();
			overwrittenFiles = new List<string>();
			timer.Start();
		}

		public static string LogText
		{
			get
			{
				string text = string.Format("VpkExtract log for {0}", DateTime.Now.ToString("hh:mm MM-dd-yyyy"));
				if (newFiles.Any())
				{
					text += Environment.NewLine + Environment.NewLine + "New Files: " + Environment.NewLine;
					text += newFiles.Aggregate((f1, f2) => f1 + Environment.NewLine + f2);
				}
				if (overwrittenFiles.Any())
				{
					text += Environment.NewLine + Environment.NewLine + "Overwritten Files: " + Environment.NewLine;
					text += overwrittenFiles.Aggregate((f1, f2) => f1 + Environment.NewLine + f2);
				}
				text += Environment.NewLine + Report;
				return text;
			}
		}

		public static void DumpLog()
		{
			string filename = Path.Combine(log_dir, string.Format("extractlog {0}.txt", DateTime.Now.ToString("mm-hh MM-dd-yyyy")));

			// If it does not exist, create dir
			Directory.CreateDirectory(Path.GetDirectoryName(filename));

			// Dump log to file
			File.WriteAllText(filename, LogText);
		}
	}
}
