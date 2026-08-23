# Constraint Comparison: Original vs FormatFuzzer Templates

This document compares the constraints extracted by LLM from the **original binary templates** (`*-orig`) versus the **FormatFuzzer-edited templates** for each file format. Each table uses a Venn-diagram layout with three columns:

- **Original Template Only** — constraints present only in the original (upstream) template
- **In Both** — constraints present in both templates (with differences noted where applicable)
- **FormatFuzzer Template Only** — constraints present only in the FormatFuzzer-edited template

Constraints in the *In Both* column that have **different values** between the two templates are annotated with `[DIFF]` and both values are shown.

---

## AVI

**Original template constraints:** 17 | **FormatFuzzer template constraints:** 22
- Constraints only in original: 6
- Constraints in both (same): 7
- Constraints in both (different values): 4
- Constraints only in FormatFuzzer: 11

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **BITMAPINFOHEADER.biPlanes**<br>Fixed: `0x0001` *(risk: high)* | **JUNKHEADER.id**<br>Fixed: `0x4A554E4B` *(risk: high)* | **AVIINDEXENTRY.dwFlags**<br>Fixed: `0x00` *(risk: medium)* |
| **MainAVIHeader.dwReserved1**<br>Fixed: `0x00000000` *(risk: low)* | **LISTHEADER.id**<br>Fixed: `0x4C495354` *(risk: high)* | **BITMAPINFOHEADER.biBitCount**<br>Fixed: `0x08` *(risk: high)* |
| **ROOT.datalen**<br>Length of RIFF chunk data in bytes - should equal file size minus 8 *(risk: medium)* | **ROOT.form**<br>Fixed: `0x41564920` *(risk: high)* | **BITMAPINFOHEADER.biCompression**<br>Fixed: `0x01` *(risk: high)* |
| **WAVEFORMATEX.wFormatTag**<br>Enum: {1, 2, 3, 6, 7, 17, 85} *(risk: high)* | **avihHEADER.id**<br>Fixed: `0x61766968` *(risk: high)* | **MOVICHUNK.id**<br>Enum: {00db, 00dc, 00pc, 00wb} *(risk: high)* |
| **avihHEADER.datalen**<br>Fixed: `0x00000038` *(risk: high)* | **idx1HEADER.id**<br>Fixed: `0x69647831` *(risk: high)* | **ROOT.root_datalen**<br>RIFF chunk size - total file size minus 8 *(risk: high)* |
| **idx1HEADER.datalen**<br>Index data length - must be a multiple of AVIINDEXENTRYLEN (16) *(risk: high)* | **strfHEADER.id**<br>Fixed: `0x73747266` *(risk: high)* | **VideoPropHeader.id**<br>Fixed: `0x76707270` *(risk: high)* |
|  | **strhHEADER.id**<br>Fixed: `0x73747268` *(risk: high)* | **VideoPropHeader.nbFieldPerFrame**<br>Enum: {1, 2} *(risk: medium)* |
|  | **AVIStreamHeader.fccType** `[DIFF]`<br>*Orig:* Enum: {vids, auds, txts, mids} *(risk: high)*<br>*FF:* Enum: {vids, auds} *(risk: high)* | **avihHEADER.avi_hdr_datalen**<br>Fixed: `0x38` *(risk: high)* |
|  | **LISTHEADER.type** `[DIFF]`<br>*Orig:* Enum: {hdrl, strl, movi, INFO, odml} *(risk: high)*<br>*FF:* Enum: {hdrl, strl, movi} *(risk: high)* | **strfHEADER_BIH.strf_hdr_bih_datalen**<br>Range: [40, 58] *(risk: medium)* |
|  | **ROOT.id** `[DIFF]`<br>*Orig:* Enum: {RIFF, RIFX} *(risk: high)*<br>*FF:* Fixed: `0x52494646` *(risk: high)* | **strfHEADER_WAVE.strf_hdr_wave_datalen**<br>Range: [20, 36] *(risk: medium)* |
|  | **strnHEADER.id** `[DIFF]`<br>*Orig:* Fixed: `0x7374726E` *(risk: medium)*<br>*FF:* Fixed: `0x76656474` *(risk: medium)* | **strhHEADER.strh_hdr_datalen**<br>Fixed: `0x38` *(risk: high)* |

---

## BMP

**Original template constraints:** 13 | **FormatFuzzer template constraints:** 12
- Constraints only in original: 1
- Constraints in both (same): 1
- Constraints in both (different values): 11
- Constraints only in FormatFuzzer: 0

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **BITMAPINFOHEADER.biClrUsed**<br>Range: [0, 256] *(risk: medium)* | **BITMAPFILEHEADER.bfType**<br>Fixed: `0x424D` *(risk: high)* |  |
|  | **BITMAPFILEHEADER.bfOffBits** `[DIFF]`<br>*Orig:* Offset from start of file to pixel data *(risk: high)*<br>*FF:* Byte offset from file start to pixel data *(risk: high)* |  |
|  | **BITMAPFILEHEADER.bfReserved1** `[DIFF]`<br>*Orig:* Fixed: `0x0000` *(risk: low)*<br>*FF:* Fixed: `0x00` *(risk: medium)* |  |
|  | **BITMAPFILEHEADER.bfReserved2** `[DIFF]`<br>*Orig:* Fixed: `0x0000` *(risk: low)*<br>*FF:* Fixed: `0x00` *(risk: medium)* |  |
|  | **BITMAPFILEHEADER.bfSize** `[DIFF]`<br>*Orig:* Total bitmap file size in bytes *(risk: medium)*<br>*FF:* Total file size in bytes - must match actual file size *(risk: high)* |  |
|  | **BITMAPINFOHEADER.biBitCount** `[DIFF]`<br>*Orig:* Enum: {1, 2, 4, 8, 16, 24, 32} *(risk: high)*<br>*FF:* Enum: {1, 4, 8, 16, 24, 32} *(risk: high)* |  |
|  | **BITMAPINFOHEADER.biCompression** `[DIFF]`<br>*Orig:* Enum: {0, 1, 2, 3, 4, 5} *(risk: high)*<br>*FF:* Enum: {0=BI_RGB, 1=BI_RLE8, 2=BI_RLE4, 3=BI_BITFIELDS} *(risk: high)* |  |
|  | **BITMAPINFOHEADER.biHeight** `[DIFF]`<br>*Orig:* Range: [-2147483648, 2147483647] *(risk: high)*<br>*FF:* Range: [1, 65535] *(risk: medium)* |  |
|  | **BITMAPINFOHEADER.biPlanes** `[DIFF]`<br>*Orig:* Fixed: `0x0001` *(risk: high)*<br>*FF:* Fixed: `0x01` *(risk: high)* |  |
|  | **BITMAPINFOHEADER.biSize** `[DIFF]`<br>*Orig:* Enum: {12, 40, 52, 56, 64, 108, 124} *(risk: high)*<br>*FF:* Fixed: `0x28` *(risk: high)* |  |
|  | **BITMAPINFOHEADER.biSizeImage** `[DIFF]`<br>*Orig:* Size of image data - may be 0 for BI_RGB but must match pixel data length when c *(risk: medium)*<br>*FF:* Size of raw bitmap data in bytes *(risk: medium)* |  |
|  | **BITMAPINFOHEADER.biWidth** `[DIFF]`<br>*Orig:* Range: [1, 2147483647] *(risk: high)*<br>*FF:* Range: [1, 65535] *(risk: medium)* |  |

---

## GIF

**Original template constraints:** 18 | **FormatFuzzer template constraints:** 20
- Constraints only in original: 2
- Constraints in both (same): 16
- Constraints in both (different values): 0
- Constraints only in FormatFuzzer: 4

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **DATASUBBLOCK.Size**<br>Sub-block size in bytes - must match the following data byte count (1..255) *(risk: high)* | **APPLICATIONEXTENTION.ApplicationLabel**<br>Fixed: `0xFF` *(risk: high)* | **IMAGEDATA.LZWMinimumCodeSize**<br>Enum: {8, 11} *(risk: high)* |
| **IMAGEDESCRIPTOR_PACKEDFIELDS.Reserved**<br>Fixed: `0x00` *(risk: medium)* | **APPLICATIONEXTENTION.ExtensionIntroducer**<br>Fixed: `0x21` *(risk: high)* | **IMAGEDESCRIPTOR.PackedFields.Reserved**<br>Fixed: `0x00` *(risk: low)* |
|  | **APPLICATIONSUBBLOCK.BlockSize**<br>Fixed: `0x0B` *(risk: high)* | **LogicalScreenDescriptor.PackedFields.Reserved**<br>Fixed: `0x00` *(risk: low)* |
|  | **COMMENTEXTENSION.CommentLabel**<br>Fixed: `0xFE` *(risk: high)* | **UNDEFINEDDATA.ExtensionIntroducer**<br>Fixed: `0x21` *(risk: high)* |
|  | **COMMENTEXTENSION.ExtensionIntroducer**<br>Fixed: `0x21` *(risk: high)* |  |
|  | **DATASUBBLOCKS.BlockTerminator**<br>Fixed: `0x00` *(risk: high)* |  |
|  | **GIFHEADER.Signature**<br>Fixed: `0x474946` *(risk: high)* |  |
|  | **GIFHEADER.Version**<br>Enum: {87a, 89a} *(risk: high)* |  |
|  | **GRAPHICCONTROLEXTENSION.BlockTerminator**<br>Fixed: `0x00` *(risk: high)* |  |
|  | **GRAPHICCONTROLEXTENSION.ExtensionIntroducer**<br>Fixed: `0x21` *(risk: high)* |  |
|  | **GRAPHICCONTROLEXTENSION.GraphicControlLabel**<br>Fixed: `0xF9` *(risk: high)* |  |
|  | **GRAPHICCONTROLSUBBLOCK.BlockSize**<br>Fixed: `0x04` *(risk: high)* |  |
|  | **IMAGEDESCRIPTOR.ImageSeperator**<br>Fixed: `0x2C` *(risk: high)* |  |
|  | **PLAINTEXTEXTENTION.ExtensionIntroducer**<br>Fixed: `0x21` *(risk: high)* |  |
|  | **PLAINTEXTEXTENTION.PlainTextLabel**<br>Fixed: `0x01` *(risk: high)* |  |
|  | **TRAILER.GIFTrailer**<br>Fixed: `0x3B` *(risk: high)* |  |

---

## JPG

**Original template constraints:** 21 | **FormatFuzzer template constraints:** 24
- Constraints only in original: 11
- Constraints in both (same): 4
- Constraints in both (different values): 6
- Constraints only in FormatFuzzer: 14

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **APP1.EXIF.byteOrder**<br>Enum: {II, MM} *(risk: high)* | **APP0.marker**<br>Fixed: `0xFFE0` *(risk: high)* | **APP0.szSection**<br>Fixed: `0x10` *(risk: high)* |
| **APP1.identifier**<br>Enum: {Exif  } *(risk: high)* | **DHT.marker**<br>Fixed: `0xFFC4` *(risk: high)* | **APP0.versionHigh**<br>Fixed: `0x01` *(risk: medium)* |
| **COMMENT.marker**<br>Fixed: `0xFFFE` *(risk: medium)* | **DQT.marker**<br>Fixed: `0xFFDB` *(risk: high)* | **APP0.versionLow**<br>Fixed: `0x01` *(risk: medium)* |
| **DRI.marker**<br>Fixed: `0xFFDD` *(risk: medium)* | **SOS.marker**<br>Fixed: `0xFFDA` *(risk: high)* | **APP0.xThumbnail**<br>Fixed: `0x00` *(risk: medium)* |
| **DRI.szSection**<br>Fixed: `0x0004` *(risk: high)* | **APP0.identifier** `[DIFF]`<br>*Orig:* Enum: {JFIF , JFXX } *(risk: high)*<br>*FF:* Fixed: `0x4A46494600` *(risk: high)* | **APP0.yThumbnail**<br>Fixed: `0x00` *(risk: medium)* |
| **JPGFILE.EOIMarker**<br>Fixed: `0xFFD9` *(risk: high)* | **APP0.units** `[DIFF]`<br>*Orig:* Enum: {0, 1, 2} *(risk: medium)*<br>*FF:* Fixed: `0x01` *(risk: medium)* | **APP2.marker**<br>Fixed: `0xFFE2` *(risk: high)* |
| **JPGFILE.SOIMarker**<br>Fixed: `0xFFD8` *(risk: high)* | **APP1.EXIF.tagMark** `[DIFF]`<br>*Orig:* Fixed: `0x002A` *(risk: high)*<br>*FF:* Fixed: `0x2A` *(risk: high)* | **COMPSOF.HorzVert**<br>Fixed: `0x11` *(risk: medium)* |
| **M_ID**<br>JPEG section markers all start with byte 0xFF followed by a non-zero marker byte *(risk: high)* | **APP1.marker** `[DIFF]`<br>*Orig:* Fixed: `0xFFE1` *(risk: high)*<br>*FF:* Fixed: `0xFFE0` *(risk: high)* | **JPGFile.StartMarker**<br>Fixed: `0xFFD8` *(risk: high)* |
| **SOFx.marker**<br>Enum: {65472=M_SOF0, 65473=M_SOF1, 65474=M_SOF2, 65475=M_SOF3} *(risk: high)* | **SOS.nr_comp** `[DIFF]`<br>*Orig:* Range: [1, 4] *(risk: high)*<br>*FF:* Enum: {1=Grayscale, 3=YCbCr} *(risk: high)* | **SOF.marker**<br>Fixed: `0xFFC0` *(risk: high)* |
| **SOFx.nr_comp**<br>Range: [1, 4] *(risk: high)* | **szSection** `[DIFF]`<br>*Orig:* Segment length (big-endian uint16) - must equal segment content size including t *(risk: high)*<br>*FF:* Segment length - must match actual segment content *(risk: high)* | **SOF.nr_comp**<br>Enum: {1=Grayscale, 3=YCbCr} *(risk: high)* |
| **SOFx.precision**<br>Enum: {8, 12, 16} *(risk: high)* |  | **SOF.precision**<br>Fixed: `0x08` *(risk: high)* |
|  |  | **SOS.AhAl**<br>Fixed: `0x00` *(risk: medium)* |
|  |  | **SOS.Se**<br>Fixed: `0x3F` *(risk: medium)* |
|  |  | **SOS.Ss**<br>Fixed: `0x00` *(risk: medium)* |

---

## MIDI

**Original template constraints:** 10 | **FormatFuzzer template constraints:** 8
- Constraints only in original: 5
- Constraints in both (same): 3
- Constraints in both (different values): 2
- Constraints only in FormatFuzzer: 3

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **DeltaTime.byte**<br>Variable-length delta-time byte (low 7 bits are value, high bit is continuation; *(risk: high)* | **MidiHeader.m_format**<br>Enum: {0=MIDI_SINGLE, 1=MIDI_MULTIPLE, 2=MIDI_PATTERN} *(risk: high)* | **DeltaTime.t0**<br>Range: [0, 127] *(risk: medium)* |
| **MidiHeader.m_seclen**<br>Fixed: `0x00000006` *(risk: high)* | **MidiHeader.m_magic**<br>Fixed: `0x4D546864` *(risk: high)* | **MidiHeader.m_seclen_hdr**<br>Fixed: `0x06` *(risk: high)* |
| **MidiHeader.m_tickdiv**<br>Range: [1, 32767] *(risk: medium)* | **MidiTrack.m_magic**<br>Fixed: `0x4D54726B` *(risk: high)* | **MidiTrack.m_seclen_trk**<br>Track section length - must match track data length *(risk: high)* |
| **MidiMessage.meta_event.m_type**<br>Enum: {0=META_SEQUENCE_NUM, 1=META_TEXT, 2=META_COPYRIGHT, 3=META_SEQUENCE_NAME, 4=META_INSTRUMENT_NAME (+13 more)} *(risk: high)* | **MidiHeader.m_ntracks** `[DIFF]`<br>*Orig:* Number of MTrk chunks following the header - must match actual track count *(risk: high)*<br>*FF:* Range: [0, 8] *(risk: medium)* |  |
| **MidiTrack.m_seclen**<br>MTrk chunk length in bytes - must equal byte size of contained events *(risk: high)* | **MidiMessage.m_status** `[DIFF]`<br>*Orig:* MIDI status byte - high bit (0x80) must be set when present; otherwise running s *(risk: high)*<br>*FF:* MIDI status byte - high bit must be set when present *(risk: high)* |  |

---

## MP3

**Original template constraints:** 15 | **FormatFuzzer template constraints:** 19
- Constraints only in original: 11
- Constraints in both (same): 2
- Constraints in both (different values): 2
- Constraints only in FormatFuzzer: 15

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **ID3v2_4_FRAME.encoding**<br>Enum: {0=ISO_8859_1, 1=UTF_16_with_BOM, 2=UTF_16BE_without_BOM, 3=UTF_8} *(risk: medium)* | **ID3v1_TAG.id**<br>Fixed: `0x544147` *(risk: high)* | **ID3v1_TAG.zero**<br>Fixed: `0x00` *(risk: medium)* |
| **ID3v2_FRAME.id**<br>ID3v2 frame identifier - 4 uppercase ASCII alphanumeric characters *(risk: high)* | **ID3v2_HEADER.head**<br>Fixed: `0x494433` *(risk: high)* | **ID3v2_HEADER.i_experiment_tag**<br>Fixed: `0x00` *(risk: low)* |
| **MPEG_HEADER.bitrate_index**<br>Range: [1, 14] *(risk: high)* | **ID3v2_HEADER.ver_major** `[DIFF]`<br>*Orig:* Enum: {2, 3, 4} *(risk: high)*<br>*FF:* Range: [3, 4] *(risk: high)* | **ID3v2_HEADER.i_extend_head_pres**<br>Fixed: `0x00` *(risk: medium)* |
| **MPEG_HEADER.channel_mode**<br>Enum: {0=Stereo, 1=JointStereo, 2=DualChannel, 3=Mono} *(risk: medium)* | **ID3v2_HEADER.ver_revision** `[DIFF]`<br>*Orig:* Range: [0, 254] *(risk: high)*<br>*FF:* Range: [2, 4] *(risk: medium)* | **ID3v2_HEADER.i_unsyn_used**<br>Fixed: `0x00` *(risk: medium)* |
| **MPEG_HEADER.emphasis**<br>Enum: {0, 1, 3} *(risk: low)* |  | **ID3v2_HEADER.reserv_flags**<br>Fixed: `0x00` *(risk: medium)* |
| **MPEG_HEADER.frame_sync**<br>Fixed: `0xFFE` *(risk: high)* |  | **ID3v2_HEADER.size**<br>Range: [0, 268435455] *(risk: high)* |
| **MPEG_HEADER.frequency_index**<br>Enum: {0, 1, 2} *(risk: high)* |  | **MPEG_FRAME.crc16**<br>Optional CRC-16 immediately following header (when protection_bit=0) *(risk: high)* |
| **MPEG_HEADER.layer_id**<br>Enum: {1, 2, 3} *(risk: high)* |  | **MPEG_HDR.bitrate_index**<br>Range: [1, 14] *(risk: high)* |
| **MPEG_HEADER.mpeg_id**<br>Enum: {1=MPEG-2, 2=MPEG-1} *(risk: high)* |  | **MPEG_HDR.emphasis**<br>Enum: {0, 1, 3} *(risk: low)* |
| **MPEG_HEADER.protection_bit**<br>Enum: {0, 1} *(risk: medium)* |  | **MPEG_HDR.frame_sync**<br>Fixed: `0x0FFF` *(risk: high)* |
| **synchsafe_integer.raw**<br>ID3v2 synchsafe integer - each byte must have MSB cleared (< 0x80) *(risk: high)* |  | **MPEG_HDR.full_hdr**<br>Composed 32-bit frame header - must match assembled subfields *(risk: high)* |
|  |  | **MPEG_HDR.layer_id**<br>Enum: {1=Layer3, 2=Layer2, 3=Layer1} *(risk: high)* |
|  |  | **MPEG_HDR.mpeg_version_id**<br>Enum: {0=MPEG_v2, 1=MPEG_v1} *(risk: high)* |
|  |  | **MPEG_HDR.protection_bit**<br>Enum: {0=protected, 1=unprotected} *(risk: medium)* |
|  |  | **MPEG_HDR.sampling_freq_index**<br>Range: [0, 2] *(risk: high)* |

---

## MP4

**Original template constraints:** 18 | **FormatFuzzer template constraints:** 35
- Constraints only in original: 12
- Constraints in both (same): 0
- Constraints in both (different values): 6
- Constraints only in FormatFuzzer: 29

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **boxheader.size**<br>Box size in bytes including the header. 1 indicates 64-bit size in size64 follow *(risk: high)* | **ftyp.major_brand** `[DIFF]`<br>*Orig:* Enum: {isom, iso2, iso3, iso4, iso5, iso6, mp41 (+17 more)} *(risk: high)*<br>*FF:* Enum: {avc1, iso2, isom, mmp4, mp41, mp42, mp71 (+12 more)} *(risk: high)* | **avc1.data_reference_index**<br>Fixed: `0x01` *(risk: high)* |
| **boxheader.size64**<br>64-bit box size present when size==1; must equal actual box length including hea *(risk: high)* | **hdlr.type** `[DIFF]`<br>*Orig:* Enum: {mhlr, dhlr,     } *(risk: medium)*<br>*FF:* Fixed: `0x68646C72` *(risk: high)* | **avc1.depth**<br>Fixed: `0x18` *(risk: medium)* |
| **boxheader.type**<br>Enum: {ftyp, moov, mvhd, trak, tkhd, edts, elst (+39 more)} *(risk: high)* | **mdhd.version** `[DIFF]`<br>*Orig:* Enum: {0, 1} *(risk: high)*<br>*FF:* Fixed: `0x00` *(risk: high)* | **avc1.frame_count**<br>Fixed: `0x01` *(risk: medium)* |
| **ftyp.minor_version**<br>Range: [0, 4294967295] *(risk: low)* | **mvhd.version** `[DIFF]`<br>*Orig:* Enum: {0, 1} *(risk: high)*<br>*FF:* Fixed: `0x00` *(risk: high)* | **avc1.horizresolution**<br>Fixed: `0x480000` *(risk: low)* |
| **hdlr.subtype**<br>Enum: {vide, soun, hint, meta, subt, text, auxv (+1 more)} *(risk: high)* | **stsd.entry_count** `[DIFF]`<br>*Orig:* Number of sample description entries in stsd box - must match number of mp4box e *(risk: high)*<br>*FF:* Fixed: `0x01` *(risk: high)* | **avc1.vertresolution**<br>Fixed: `0x480000` *(risk: low)* |
| **mdhd.language**<br>Packed ISO-639-2/T language code (3 lowercase letters), each letter encoded as 5 *(risk: low)* | **tkhd.version** `[DIFF]`<br>*Orig:* Enum: {0, 1} *(risk: high)*<br>*FF:* Fixed: `0x00` *(risk: high)* | **avcC.configurationVersion**<br>Fixed: `0x01` *(risk: high)* |
| **qtgfxmode**<br>Enum: {0=qtgCopy, 32=qtgBlend, 36=qtgTransparent, 64=qtgDitherCopy, 256=qtgStraightAlpha (+4 more)} *(risk: medium)* |  | **avcC.reserved_lengthSizeMinusOne**<br>Enum: {252, 253, 254, 255} *(risk: medium)* |
| **stco.chunk_offset**<br>Range: [0, 4294967295] *(risk: high)* |  | **avcC.reserved_numOfSequenceParameterSets**<br>Fixed: `0xE1` *(risk: medium)* |
| **stsz.sample_size**<br>If non-zero, all samples have this size; if zero, individual entry_size[] table  *(risk: high)* |  | **esds.sectionID_3**<br>Fixed: `0x03808080` *(risk: high)* |
| **tkhd.reserved**<br>Fixed: `0x00000000` *(risk: low)* |  | **esds.sectionID_4**<br>Fixed: `0x04808080` *(risk: high)* |
| **tkhd.reserved2**<br>Fixed: `0x0000000000000000` *(risk: low)* |  | **esds.sectionID_5**<br>Fixed: `0x05808080` *(risk: high)* |
| **tkhd.reserved3**<br>Fixed: `0x0000` *(risk: low)* |  | **esds.sectionID_6**<br>Fixed: `0x06808080` *(risk: high)* |
|  |  | **ftyp.compatible_brands**<br>Enum: {isom, iso2, avc1, mp41} *(risk: medium)* |
|  |  | **ftyp.major_version**<br>Fixed: `0x0200` *(risk: medium)* |
|  |  | **ftyp.type**<br>Fixed: `0x66747970` *(risk: high)* |
|  |  | **hdlr.handler_type_audio**<br>Fixed: `0x736F756E` *(risk: high)* |
|  |  | **hdlr.handler_type_video**<br>Fixed: `0x76696465` *(risk: high)* |
|  |  | **hdlr.pre_defined**<br>Fixed: `0x00` *(risk: medium)* |
|  |  | **hdlr.reserved_audio**<br>Fixed: `0x00` *(risk: medium)* |
|  |  | **hdlr.reserved_video**<br>Fixed: `0x6170706C00000000` *(risk: medium)* |
|  |  | **mdhd.type**<br>Fixed: `0x6D646864` *(risk: high)* |
|  |  | **mp4a.channelcount**<br>Fixed: `0x02` *(risk: medium)* |
|  |  | **mp4a.data_reference_index**<br>Fixed: `0x01` *(risk: high)* |
|  |  | **mp4a.samplesize**<br>Fixed: `0x10` *(risk: medium)* |
|  |  | **mvhd.type**<br>Fixed: `0x6D766864` *(risk: high)* |
|  |  | **size**<br>Box size - must be set to actual box length after content is written *(risk: high)* |
|  |  | **tkhd.duration_tkhd**<br>Range: [3, 4294967295] *(risk: medium)* |
|  |  | **tkhd.type**<br>Fixed: `0x746B6864` *(risk: high)* |
|  |  | **vmhd.graphics_mode**<br>Fixed: `0x00` *(risk: medium)* |

---

## PCAP

**Original template constraints:** 15 | **FormatFuzzer template constraints:** 15
- Constraints only in original: 5
- Constraints in both (same): 1
- Constraints in both (different values): 9
- Constraints only in FormatFuzzer: 5

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **Layer_4.tcp_hdr_len**<br>Range: [5, 15] *(risk: high)* | **PCAPHEADER.magic_number**<br>Fixed: `0xA1B2C3D4` *(risk: high)* | **Dot1q.L3type**<br>Fixed: `0x0800` *(risk: high)* |
| **PCAPHEADER.sigfigs**<br>Fixed: `0x00000000` *(risk: low)* | **Layer_2.L3type** `[DIFF]`<br>*Orig:* Enum: {2048=IPv4, 2054=ARP, 34525=IPv6, 33024=802.1Q} *(risk: high)*<br>*FF:* Enum: {2048=IPv4, 33024=802.1Q VLAN} *(risk: high)* | **Layer_4_TCP.data_offset**<br>Fixed: `0x05` *(risk: high)* |
| **PCAPHEADER.thiszone**<br>Fixed: `0x00000000` *(risk: low)* | **Layer_3.L4proto** `[DIFF]`<br>*Orig:* Enum: {1=ICMP, 6=TCP, 17=UDP, 47=GRE, 50=ESP (+3 more)} *(risk: high)*<br>*FF:* Enum: {6=TCP, 17=UDP} *(risk: high)* | **Layer_4_UDP.udp_hdr_len**<br>UDP datagram length - must match payload length + 8 *(risk: high)* |
| **PCAPRECORD.incl_len**<br>Bytes of packet stored in file - must equal length of packet data following the  *(risk: high)* | **Layer_3.ip_hdr_len** `[DIFF]`<br>*Orig:* Range: [5, 15] *(risk: high)*<br>*FF:* Fixed: `0x05` *(risk: high)* | **PCAPRecord.incl_len**<br>Captured packet length - must match actual frame size *(risk: high)* |
| **PCAPRECORD.orig_len**<br>Range: [0, 4294967295] *(risk: medium)* | **Layer_3.total_length** `[DIFF]`<br>*Orig:* Total IPv4 datagram length - must be >= header length and consistent with captur *(risk: high)*<br>*FF:* Range: [40, 104] *(risk: medium)* | **PCAPRecord.orig_len**<br>Original packet length - should match incl_len *(risk: high)* |
|  | **Layer_3.version** `[DIFF]`<br>*Orig:* Enum: {4, 6} *(risk: high)*<br>*FF:* Fixed: `0x04` *(risk: high)* |  |
|  | **PCAPHEADER.network** `[DIFF]`<br>*Orig:* Enum: {0, 1, 101, 105, 113, 127, 147 (+2 more)} *(risk: high)*<br>*FF:* Enum: {1=LINKTYPE_ETHERNET, 101=LINKTYPE_RAW} *(risk: high)* |  |
|  | **PCAPHEADER.snaplen** `[DIFF]`<br>*Orig:* Range: [1, 262144] *(risk: medium)*<br>*FF:* Range: [256, 1024] *(risk: medium)* |  |
|  | **PCAPHEADER.version_major** `[DIFF]`<br>*Orig:* Fixed: `0x0002` *(risk: high)*<br>*FF:* Fixed: `0x02` *(risk: high)* |  |
|  | **PCAPHEADER.version_minor** `[DIFF]`<br>*Orig:* Fixed: `0x0004` *(risk: high)*<br>*FF:* Enum: {2, 4} *(risk: medium)* |  |

---

## PNG

**Original template constraints:** 20 | **FormatFuzzer template constraints:** 19
- Constraints only in original: 1
- Constraints in both (same): 17
- Constraints in both (different values): 2
- Constraints only in FormatFuzzer: 0

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **PNG_COMPR_METHOD.itxtComprMethod**<br>Fixed: `0x00` *(risk: medium)* | **PNG_CHUNK.crc**<br>CRC-32 of chunk type and data - must match calculated value *(risk: high)* |  |
|  | **PNG_CHUNK.length**<br>Chunk data length - must match actual data byte count *(risk: high)* |  |
|  | **PNG_CHUNK.type**<br>Enum: {IHDR, PLTE, IDAT, IEND, tRNS, cHRM, gAMA (+15 more)} *(risk: high)* |  |
|  | **PNG_CHUNK_IHDR.bits**<br>Enum: {1, 2, 4, 8, 16} *(risk: high)* |  |
|  | **PNG_CHUNK_IHDR.color_type**<br>Enum: {0=GrayScale, 2=TrueColor, 3=Indexed, 4=AlphaGrayScale, 6=AlphaTrueColor} *(risk: high)* |  |
|  | **PNG_CHUNK_IHDR.compr_method**<br>Fixed: `0x00` *(risk: high)* |  |
|  | **PNG_CHUNK_IHDR.filter_method**<br>Fixed: `0x00` *(risk: high)* |  |
|  | **PNG_CHUNK_IHDR.interlace_method**<br>Enum: {0=NoInterlace, 1=Adam7Interlace} *(risk: high)* |  |
|  | **PNG_CHUNK_TIME.timeDay**<br>Range: [1, 31] *(risk: low)* |  |
|  | **PNG_CHUNK_TIME.timeHour**<br>Range: [0, 23] *(risk: low)* |  |
|  | **PNG_CHUNK_TIME.timeMin**<br>Range: [0, 59] *(risk: low)* |  |
|  | **PNG_CHUNK_TIME.timeMonth**<br>Range: [1, 12] *(risk: low)* |  |
|  | **PNG_CHUNK_TIME.timeSec**<br>Range: [0, 60] *(risk: low)* |  |
|  | **PNG_SIGNATURE.btPngSignature[0]**<br>Fixed: `0x8950` *(risk: high)* |  |
|  | **PNG_SIGNATURE.btPngSignature[1]**<br>Fixed: `0x4E47` *(risk: high)* |  |
|  | **PNG_SIGNATURE.btPngSignature[2]**<br>Fixed: `0x0D0A` *(risk: high)* |  |
|  | **PNG_SIGNATURE.btPngSignature[3]**<br>Fixed: `0x1A0A` *(risk: high)* |  |
|  | **PNG_CHUNK_IHDR.height** `[DIFF]`<br>*Orig:* Range: [1, 2147483647] *(risk: high)*<br>*FF:* Range: [1, 24] *(risk: medium)* |  |
|  | **PNG_CHUNK_IHDR.width** `[DIFF]`<br>*Orig:* Range: [1, 2147483647] *(risk: high)*<br>*FF:* Range: [1, 24] *(risk: medium)* |  |

---

## WAV

**Original template constraints:** 17 | **FormatFuzzer template constraints:** 17
- Constraints only in original: 2
- Constraints in both (same): 4
- Constraints in both (different values): 11
- Constraints only in FormatFuzzer: 2

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **FORMATCHUNK.dwAvgBytesPerSec**<br>Average bytes per second = dwSamplesPerSec * wBlockAlign *(risk: high)* | **DATACHUNK.chunkID**<br>Fixed: `0x64617461` *(risk: high)* | **CUECHUNK.dwCuePoints**<br>Range: [1, 16] *(risk: medium)* |
| **FORMATCHUNK.dwSamplesPerSec**<br>Enum: {8000, 11025, 16000, 22050, 32000, 44100, 48000 (+4 more)} *(risk: high)* | **FORMATCHUNK.chunkID**<br>Fixed: `0x666D7420` *(risk: high)* | **FACTCHUNK.chunkSize**<br>Fixed: `0x0C` *(risk: high)* |
|  | **WAVRIFFHEADER.groupID**<br>Fixed: `0x52494646` *(risk: high)* |  |
|  | **WAVRIFFHEADER.riffType**<br>Fixed: `0x57415645` *(risk: high)* |  |
|  | **CUECHUNK.chunkID** `[DIFF]`<br>*Orig:* Fixed: `0x63756520` *(risk: medium)*<br>*FF:* Fixed: `0x63756520` *(risk: high)* |  |
|  | **DATACHUNK.chunkSize** `[DIFF]`<br>*Orig:* Size of waveform sample data - must be a multiple of wBlockAlign *(risk: high)*<br>*FF:* Data chunk size - must match length of PCM payload *(risk: high)* |  |
|  | **FACTCHUNK.chunkID** `[DIFF]`<br>*Orig:* Fixed: `0x66616374` *(risk: medium)*<br>*FF:* Fixed: `0x66616374` *(risk: high)* |  |
|  | **FORMATCHUNK.chunkSize** `[DIFF]`<br>*Orig:* Enum: {16, 18, 20, 40} *(risk: high)*<br>*FF:* Fixed: `0x10` *(risk: high)* |  |
|  | **FORMATCHUNK.wBitsPerSample** `[DIFF]`<br>*Orig:* Enum: {8, 16, 24, 32} *(risk: high)*<br>*FF:* Enum: {8, 16, 32} *(risk: high)* |  |
|  | **FORMATCHUNK.wBlockAlign** `[DIFF]`<br>*Orig:* Block alignment = wChannels * wBitsPerSample / 8 *(risk: high)*<br>*FF:* Block alignment - must equal (wBitsPerSample / 8) * wChannels *(risk: high)* |  |
|  | **FORMATCHUNK.wChannels** `[DIFF]`<br>*Orig:* Range: [1, 8] *(risk: high)*<br>*FF:* Range: [1, 256] *(risk: medium)* |  |
|  | **FORMATCHUNK.wFormatTag** `[DIFF]`<br>*Orig:* Enum: {1=PCM, 2=ADPCM, 3=IEEE_FLOAT, 6=ALAW, 7=MULAW (+2 more)} *(risk: high)*<br>*FF:* Enum: {1=PCM} *(risk: high)* |  |
|  | **LISTCHUNK.chunkID** `[DIFF]`<br>*Orig:* Fixed: `0x4C495354` *(risk: medium)*<br>*FF:* Fixed: `0x4C495354` *(risk: high)* |  |
|  | **SMPLCHUNK.chunkID** `[DIFF]`<br>*Orig:* Fixed: `0x736D706C` *(risk: medium)*<br>*FF:* Fixed: `0x736D706C` *(risk: high)* |  |
|  | **WAVRIFFHEADER.hsize** `[DIFF]`<br>*Orig:* Total RIFF chunk size in bytes - should equal file size minus 8 *(risk: medium)*<br>*FF:* RIFF chunk size - total file size minus 8 *(risk: high)* |  |

---

## ZIP

**Original template constraints:** 22 | **FormatFuzzer template constraints:** 21
- Constraints only in original: 12
- Constraints in both (same): 7
- Constraints in both (different values): 3
- Constraints only in FormatFuzzer: 11

| Original Template Only | In Both | FormatFuzzer Template Only |
|------------------------|---------|---------------------------|
| **AESMODE**<br>Enum: {1, 2, 3} *(risk: high)* | **ZIP64ENDLOCATOR.elSignature**<br>Fixed: `0x07064B50` *(risk: high)* | **ZIPDIRENTRY.deCompressedSize**<br>Must mirror the matching local file record compressed size *(risk: high)* |
| **ALGFLAG**<br>Enum: {26113, 26114, 26115, 26121, 26126, 26127, 26128 (+5 more)} *(risk: high)* | **ZIP64ENDLOCATORRECORD.elr64Signature**<br>Fixed: `0x06064B50` *(risk: high)* | **ZIPDIRENTRY.deCompression**<br>Must mirror the matching local file record compression method *(risk: high)* |
| **COMPTYPE**<br>Enum: {0, 1, 2, 3, 4, 5, 6 (+12 more)} *(risk: high)* | **ZIPDATADESCR.ddSignature**<br>Fixed: `0x08074B50` *(risk: high)* | **ZIPDIRENTRY.deCrc**<br>Must mirror the matching local file record CRC *(risk: high)* |
| **EXTRAFIELD.efDataSize**<br>Size of extra field data section in bytes - must match length of efData payload *(risk: high)* | **ZIPDIGITALSIG.dsSignature**<br>Fixed: `0x05054B50` *(risk: high)* | **ZIPDIRENTRY.deDiskNumberStart**<br>Fixed: `0x00` *(risk: medium)* |
| **EXTRAFIELD.efHeaderID**<br>Enum: {1, 7, 8, 9, 10, 12, 13 (+39 more)} *(risk: medium)* | **ZIPDIRENTRY.deSignature**<br>Fixed: `0x02014B50` *(risk: high)* | **ZIPDIRENTRY.deHeaderOffset**<br>Offset of matching local file header from start of archive *(risk: high)* |
| **HOSTOSTYPE**<br>Enum: {0=FAT, 1=AMIGA, 2=VMS, 3=Unix, 4=VM_CMS (+15 more)} *(risk: medium)* | **ZIPENDLOCATOR.elSignature**<br>Fixed: `0x06054B50` *(risk: high)* | **ZIPDIRENTRY.deUncompressedSize**<br>Must mirror the matching local file record uncompressed size *(risk: high)* |
| **PRCFLAG**<br>Enum: {1, 2, 3} *(risk: medium)* | **ZIPFILERECORD.frSignature**<br>Fixed: `0x04034B50` *(risk: high)* | **ZIPENDLOCATOR.elDiskNumber**<br>Fixed: `0x00` *(risk: medium)* |
| **SignatureTYPE**<br>Enum: {67324752=S_ZIPFILERECORD (0x04034B50 'PK\x03\x04'), 134695760=S_ZIPDATADESCR (0x08074B50 'PK\x07\x08'), 33639248=S_ZIPDIRENTRY (0x02014B50 'PK\x01\x02'), 84233040=S_ZIPDIGITALSIG (0x05054B50 'PK\x05\x05'), 101075792=S_ZIP64ENDLOCATORRECORD (0x06064B50 'PK\x06\x06') (+2 more)} *(risk: high)* | **ZIP64ENDLOCATORRECORD.elr64DirectoryRecordSize** `[DIFF]`<br>*Orig:* Size of the ZIP64 end of central directory record minus 12 (the size + signature *(risk: high)*<br>*FF:* Range: [0, 52] *(risk: medium)* | **ZIPENDLOCATOR.elStartDiskNumber**<br>Fixed: `0x00` *(risk: medium)* |
| **WzAES.VendorID**<br>Fixed: `0x4145` *(risk: high)* | **ZIPFILERECORD.frCompressedSize** `[DIFF]`<br>*Orig:* Length in bytes of compressed file data following the header - must match actual *(risk: high)*<br>*FF:* Compressed payload size *(risk: high)* | **ZIPFILERECORD.frCompression**<br>Enum: {0=COMP_STORED, 8=COMP_DEFLATE} *(risk: high)* |
| **ZIPENDLOCATOR.elCommentLength**<br>Length of the .ZIP file comment - must equal actual size of elComment field *(risk: medium)* | **ZIPFILERECORD.frFileNameLength** `[DIFF]`<br>*Orig:* Length of file name - must equal actual size of frFileName field *(risk: high)*<br>*FF:* Length of the file name in bytes *(risk: high)* | **ZIPFILERECORD.frCrc**<br>CRC-32 of uncompressed data - must match payload *(risk: high)* |
| **ZIPENDLOCATOR.elDirectoryOffset**<br>Offset of start of central directory - must point to a valid ZIPDIRENTRY signatu *(risk: high)* |  | **ZIPFILERECORD.frUncompressedSize**<br>Uncompressed payload size *(risk: high)* |
| **ZIPFILERECORD.frExtraFieldLength**<br>Sum of EXTRAFIELD (efDataSize + 4) entries must equal frExtraFieldLength *(risk: high)* |  |  |

---
