using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ValveResourceFormat;
using ValveResourceFormat.ResourceTypes;

namespace Extractor
{
    class Program
    {
        const string vpk_destination = "...";
        static void Main(string[] args)
        {
            var package = new Package();
            package.Read("C:\\Program Files (x86)\\Steam\\steamapps\\common\\dota 2 beta\\game\\dota\\pak01_dir.vpk");

            var entries = package.Entries["vsnd_c"];

            //var entries = package.Entries["png"];

            foreach (var file in entries)
            {
                var filePath = string.Format("{0}.{1}", file.FileName, file.TypeName);

                filePath = Path.Combine(file.DirectoryName, filePath);

                byte[] fileData;
                package.ReadEntry(file, out fileData);
                
                filePath = Path.Combine(vpk_destination, filePath);

                //DumpFile(filePath, fileData);

                using (var resource = new Resource())
                {
                    using (var memory = new MemoryStream(fileData))
                    {
                        resource.Read(memory);
                        ProcessFile(filePath, resource);
                    }
                }
            }
        }


        private static void ProcessFile(string path, Resource resource)
        {
            string extension = Path.GetExtension(path);

            if (extension.EndsWith("_c", StringComparison.Ordinal))
            {
                extension = extension.Substring(0, extension.Length - 2);
            }

            byte[] data;

            switch (resource.ResourceType)
            {
                case ResourceType.Panorama:
                    data = ((Panorama)resource.Blocks[BlockType.DATA]).Data;
                    break;

                case ResourceType.Sound:
                    var sound = ((Sound)resource.Blocks[BlockType.DATA]);

                    switch (sound.Type)
                    {
                        case Sound.AudioFileType.MP3:
                            extension = "mp3";
                            break;

                        case Sound.AudioFileType.WAV:
                            extension = "wav";
                            break;
                    }

                    data = sound.GetSound();

                    break;

                case ResourceType.Texture:
                    extension = "png";

                    var bitmap = ((Texture)resource.Blocks[BlockType.DATA]).GenerateBitmap();

                    using (var ms = new MemoryStream())
                    {
                        bitmap.Save(ms, System.Drawing.Imaging.ImageFormat.Png);

                        data = ms.ToArray();
                    }

                    break;
                case ResourceType.Particle:
                case ResourceType.Mesh:
                    //Wrap it around a KV3File object to get the header.
                    data = Encoding.UTF8.GetBytes(new ValveResourceFormat.KeyValues.KV3File(((BinaryKV3)resource.Blocks[BlockType.DATA]).Data).ToString());
                    break;

                //These all just use ToString() and WriteText() to do the job
                case ResourceType.SoundEventScript:
                    data = Encoding.UTF8.GetBytes(resource.Blocks[BlockType.DATA].ToString());
                    break;

                default:
                    Console.WriteLine("-- (I don't know how to dump this resource type)");
                    return;
            }

            path = Path.ChangeExtension(path, extension);

            DumpFile(path, data);
        }



        private static void DumpFile(string path, byte[] data)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));

            Console.WriteLine("Wrote: " + path);

            File.WriteAllBytes(path, data);
        }

    }
}
