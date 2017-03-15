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

		public void Start(int total)
		{
			this.total = total;
			count = 0;
		}

		public void Inc()
		{
			count++;
		}

		public void Print()
		{
			Console.WriteLine("({0}/{1})", count, total);
		}
	}
}
