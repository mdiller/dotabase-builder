using System;
using System.IO;
using System.Text;
using System.Linq;
using ValveResourceFormat;
using ValveResourceFormat.ResourceTypes;
using SteamDatabase.ValvePak;

namespace VpkExtractor
{
	/// <summary>
	/// Represents a file to be extracted from a vpk
	/// </summary>
	public class EntryFile
	{
		public PackageEntry entry;
		public byte[] data;
		private string extension;

		public string vpkpath
		{
			get { return Path.Combine(entry.DirectoryName ?? "", string.Format("{0}.{1}", entry.FileName, entry.TypeName)); }
		}

		public string outfile
		{
			get { return Path.ChangeExtension(Path.Combine(Extractor.config.vpk_path, vpkpath), extension); }
		}

		/// <summary>
		/// Initializes a new entryfile from a packageentry and whether or not we should convert this entryfile
		/// </summary>
		/// <param name="entry">the packageentry that this entryfile represents</param>
		/// <param name="convert">whether or not to convert this packageentry</param>
		public EntryFile(PackageEntry entry, string newExtension, bool convert)
		{
			this.entry = entry;
			extension = newExtension ?? entry.TypeName;

			LoadData(convert);
		}

		/// <summary>
		/// Loads the file data from the vpk
		/// </summary>
		/// <param name="convert">Whether or not this file data should be converted</param>
		private void LoadData(bool convert)
		{
			Extractor.package.ReadEntry(entry, out data);

			if (!convert) { return; }

			// -- Need to convert if we get this far
			//Start by getting a resource object for this entry
			Resource resource = new Resource();
			MemoryStream mstream = new MemoryStream(data);

			resource.Read(mstream);
			
			// Fix extension weirdness
			if (extension.EndsWith("_c", StringComparison.Ordinal))
				extension = extension.Substring(0, extension.Length - 2);

			switch (resource.ResourceType)
			{
				case ResourceType.Panorama:
				case ResourceType.PanoramaScript:
				case ResourceType.PanoramaStyle:
				case ResourceType.PanoramaLayout:
					switch (entry.TypeName)
					{
						case "vxml_c":
							extension = "xml";
							data = ((Panorama)resource.Blocks[BlockType.DATA]).Data;
							break;
						case "vcss_c":
							extension = "css";
							data = ((Panorama)resource.Blocks[BlockType.DATA]).Data;
							break;
						case "vjs_c":
							extension = "js";
							data = ((Panorama)resource.Blocks[BlockType.DATA]).Data;
							break;
						default:
							throw new Exception("invalid type for panoramastuff");
					}
					break;

				case ResourceType.Sound:
					var sound = ((Sound)resource.Blocks[BlockType.DATA]);
					data = sound.GetSound();
					switch (sound.Type)
					{
						case Sound.AudioFileType.MP3:
							extension = "mp3";
							break;
						case Sound.AudioFileType.WAV:
							extension = "wav";
							break;
					}
					break;
				case ResourceType.Texture:
					extension = "png";
					var bitmap = ((Texture)resource.Blocks[BlockType.DATA]).GenerateBitmap();
					using (var stream = new MemoryStream())
					{
						bitmap.Save(stream, System.Drawing.Imaging.ImageFormat.Png);
						data = stream.ToArray();
					}
					break;
				case ResourceType.Particle:
				case ResourceType.Mesh:
					//Wrap it around a KV3File object to get the header.
					data = Encoding.UTF8.GetBytes(new ValveResourceFormat.KeyValues.KV3File(((BinaryKV3)resource.Blocks[BlockType.DATA]).Data).ToString());
					break;
				case ResourceType.SoundEventScript:
					data = Encoding.UTF8.GetBytes(resource.Blocks[BlockType.DATA].ToString());
					break;
				default:
					throw new Exception("Unexpected resource type: " + resource.ResourceType);
			}
			mstream.Dispose();
			resource.Dispose();
		}

		/// <summary>
		/// Dumps the file to the output location
		/// </summary>
		/// <param name="overwrite">Whehter or not to overwrite the file if it exists and is the same</param>
		public void Dump(bool overwrite = false)
		{
			if(!File.Exists(outfile))
			{
				Logger.LogNewFile(outfile);
			}
			else if(overwrite || !File.ReadAllBytes(outfile).SequenceEqual(data))
			{
				Logger.LogOverwriteFile(outfile);
			}
			else
			{
				// File is the same, and overwrite is false, so do nothing
				return;
			}

			// If it does not exist, create dir
			Directory.CreateDirectory(Path.GetDirectoryName(outfile)); 

			// Write all data to file
			File.WriteAllBytes(outfile, data);
		}
	}
}
