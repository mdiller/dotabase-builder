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
        private int totalChunks;
        private int count;

        private int chunkSize
        {
            get { return total / totalChunks; }
        }

        public void Start(int total, int totalChunks)
        {
            this.total = total;
            this.totalChunks = totalChunks;
            count = 0;
        }

        public void Inc()
        {
            count++;
            if (count == total || count % chunkSize == 0)
                Print();
        }

        public void Print()
        {
            Console.WriteLine("({0}/{1})", count, total);
        }
    }
}
