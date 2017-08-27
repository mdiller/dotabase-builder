using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace VpkExtractor
{
	/// <summary>
	/// Prints the progress of the current operation
	/// </summary>
	public class Progress
	{
		private int total;
		private int count;
        private int maxchunks;
        private string title;
        private ConsoleColor fill_color;
        private ConsoleColor empty_color;

		public void Start(string title, int total)
		{
            this.title = title;
			this.total = total;
			count = 0;
            maxchunks = 10;
            fill_color = Console.ForegroundColor;
            empty_color = Console.BackgroundColor;
        }

        public int percent
        {
            get
            {
                return (100 * count) / total;
            }
        }

		public void Inc()
		{
            int old_percent = percent;
			count++;
            if (old_percent != percent)
            {
                Print();
            }
		}

		public void Print()
		{
            int position = 0;
            Console.CursorLeft = position;
            string full_title = title + " |";
            Console.Write(full_title);
            position = full_title.Length;
            for (int i = 0; i < maxchunks; i++)
            {
                Console.CursorLeft = position++;
                Console.BackgroundColor = i <= ((percent / 100.0) * maxchunks) ? fill_color : empty_color;
                Console.Write(" ");
            }
            Console.BackgroundColor = empty_color;
            Console.CursorLeft = position++;
            Console.Write("|");
            Console.CursorLeft = position++;
            Console.Write(percent + "%");
            if(count == total)
            {
                Console.WriteLine();
            }
        }
	}
}
