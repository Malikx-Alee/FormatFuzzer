#include <cstdlib>
#include <cstdio>
#include <string>
#include <vector>
#include <unordered_map>
#include "bt.h"

enum e_framesync : uint32 {
	frame_sync = (uint32) 0xFFF,
};
std::vector<uint32> e_framesync_values = { frame_sync };

typedef enum e_framesync E_FRAMESYNC;
std::vector<uint32> E_FRAMESYNC_values = { frame_sync };

enum e_mpegVersion : uint32 {
	mpegv2 = (uint32) 0,
	mpegv1 = (uint32) 1,
};
std::vector<uint32> e_mpegVersion_values = { mpegv2, mpegv1 };

typedef enum e_mpegVersion E_MPEGVERSION;
std::vector<uint32> E_MPEGVERSION_values = { mpegv2, mpegv1 };

enum e_layerVersion : uint32 {
	layer3 = (uint32) 1,
	layer2 = (uint32) 2,
	layer1 = (uint32) 3,
};
std::vector<uint32> e_layerVersion_values = { layer3, layer2, layer1 };

typedef enum e_layerVersion E_LAYERVERSION;
std::vector<uint32> E_LAYERVERSION_values = { layer3, layer2, layer1 };

enum e_protectionBit : uint32 {
	protect = (uint32) 0,
	unprotect = (uint32) 1,
};
std::vector<uint32> e_protectionBit_values = { protect, unprotect };

typedef enum e_protectionBit E_PROTECTIONBIT;
std::vector<uint32> E_PROTECTIONBIT_values = { protect, unprotect };

enum e_bitRateIndexV1L1 : uint32 {
	brFreeV1L1 = (uint32) 0,
	br32V1L1 = (uint32) 1,
	br64V1L1 = (uint32) 2,
	br96V1L1 = (uint32) 3,
	br128V1L1 = (uint32) 4,
	br160V1L1 = (uint32) 5,
	br192V1L1 = (uint32) 6,
	br224V1L1 = (uint32) 7,
	br256V1L1 = (uint32) 8,
	br288V1L1 = (uint32) 9,
	br320V1L1 = (uint32) 10,
	br352V1L1 = (uint32) 11,
	br384V1L1 = (uint32) 12,
	br416V1L1 = (uint32) 13,
	br448V1L1 = (uint32) 14,
};
std::vector<uint32> e_bitRateIndexV1L1_values = { brFreeV1L1, br32V1L1, br64V1L1, br96V1L1, br128V1L1, br160V1L1, br192V1L1, br224V1L1, br256V1L1, br288V1L1, br320V1L1, br352V1L1, br384V1L1, br416V1L1, br448V1L1 };

typedef enum e_bitRateIndexV1L1 E_BITRATEINDEXV1L1;
std::vector<uint32> E_BITRATEINDEXV1L1_values = { brFreeV1L1, br32V1L1, br64V1L1, br96V1L1, br128V1L1, br160V1L1, br192V1L1, br224V1L1, br256V1L1, br288V1L1, br320V1L1, br352V1L1, br384V1L1, br416V1L1, br448V1L1 };

enum e_bitRateIndexV1L2 : uint32 {
	brFreeV1L2 = (uint32) 0,
	br32V1L2 = (uint32) 1,
	br48V1L2 = (uint32) 2,
	br56V1L2 = (uint32) 3,
	br64V1L2 = (uint32) 4,
	br80V1L2 = (uint32) 5,
	br96V1L2 = (uint32) 6,
	br112V1L2 = (uint32) 7,
	br128V1L2 = (uint32) 8,
	br160V1L2 = (uint32) 9,
	br192V1L2 = (uint32) 10,
	br224V1L2 = (uint32) 11,
	br256V1L2 = (uint32) 12,
	br320V1L2 = (uint32) 13,
	br384V1L2 = (uint32) 14,
};
std::vector<uint32> e_bitRateIndexV1L2_values = { brFreeV1L2, br32V1L2, br48V1L2, br56V1L2, br64V1L2, br80V1L2, br96V1L2, br112V1L2, br128V1L2, br160V1L2, br192V1L2, br224V1L2, br256V1L2, br320V1L2, br384V1L2 };

typedef enum e_bitRateIndexV1L2 E_BITRATEINDEXV1L2;
std::vector<uint32> E_BITRATEINDEXV1L2_values = { brFreeV1L2, br32V1L2, br48V1L2, br56V1L2, br64V1L2, br80V1L2, br96V1L2, br112V1L2, br128V1L2, br160V1L2, br192V1L2, br224V1L2, br256V1L2, br320V1L2, br384V1L2 };

enum e_bitRateIndexV1L3 : uint32 {
	brFreeV1L3 = (uint32) 0,
	br32V1L3 = (uint32) 1,
	br40V1L3 = (uint32) 2,
	br48V1L3 = (uint32) 3,
	br56V1L3 = (uint32) 4,
	br64V1L3 = (uint32) 5,
	br80V1L3 = (uint32) 6,
	br96V1L3 = (uint32) 7,
	br112V1L3 = (uint32) 8,
	br128V1L3 = (uint32) 9,
	br160V1L3 = (uint32) 10,
	br192V1L3 = (uint32) 11,
	br224V1L3 = (uint32) 12,
	br256V1L3 = (uint32) 13,
	br320V1L3 = (uint32) 14,
};
std::vector<uint32> e_bitRateIndexV1L3_values = { brFreeV1L3, br32V1L3, br40V1L3, br48V1L3, br56V1L3, br64V1L3, br80V1L3, br96V1L3, br112V1L3, br128V1L3, br160V1L3, br192V1L3, br224V1L3, br256V1L3, br320V1L3 };

typedef enum e_bitRateIndexV1L3 E_BITRATEINDEXV1L3;
std::vector<uint32> E_BITRATEINDEXV1L3_values = { brFreeV1L3, br32V1L3, br40V1L3, br48V1L3, br56V1L3, br64V1L3, br80V1L3, br96V1L3, br112V1L3, br128V1L3, br160V1L3, br192V1L3, br224V1L3, br256V1L3, br320V1L3 };

enum e_bitRateIndexV2L1 : uint32 {
	brFreeV2L1 = (uint32) 0,
	br32V2L1 = (uint32) 1,
	br48V2L1 = (uint32) 2,
	br56V2L1 = (uint32) 3,
	br64V2L1 = (uint32) 4,
	br80V2L1 = (uint32) 5,
	br96V2L1 = (uint32) 6,
	br112V2L1 = (uint32) 7,
	br128V2L1 = (uint32) 8,
	br144V2L1 = (uint32) 9,
	br160V2L1 = (uint32) 10,
	br176V2L1 = (uint32) 11,
	br192V2L1 = (uint32) 12,
	br224V2L1 = (uint32) 13,
	br256V2L1 = (uint32) 14,
};
std::vector<uint32> e_bitRateIndexV2L1_values = { brFreeV2L1, br32V2L1, br48V2L1, br56V2L1, br64V2L1, br80V2L1, br96V2L1, br112V2L1, br128V2L1, br144V2L1, br160V2L1, br176V2L1, br192V2L1, br224V2L1, br256V2L1 };

typedef enum e_bitRateIndexV2L1 E_BITRATEINDEXV2L1;
std::vector<uint32> E_BITRATEINDEXV2L1_values = { brFreeV2L1, br32V2L1, br48V2L1, br56V2L1, br64V2L1, br80V2L1, br96V2L1, br112V2L1, br128V2L1, br144V2L1, br160V2L1, br176V2L1, br192V2L1, br224V2L1, br256V2L1 };

enum e_bitRateIndexV2L2L3 : uint32 {
	brFreeV2L2L3 = (uint32) 0,
	br8V2L2L3 = (uint32) 1,
	br16V2L2L3 = (uint32) 2,
	br24V2L2L3 = (uint32) 3,
	br32V2L2L3 = (uint32) 4,
	br40V2L2L3 = (uint32) 5,
	br48V2L2L3 = (uint32) 6,
	br56V2L2L3 = (uint32) 7,
	br64V2L2L3 = (uint32) 8,
	br80V2L2L3 = (uint32) 9,
	br96V2L2L3 = (uint32) 10,
	br112V2L2L3 = (uint32) 11,
	br128V2L2L3 = (uint32) 12,
	br144V2L2L3 = (uint32) 13,
	br160V2L2L3 = (uint32) 14,
};
std::vector<uint32> e_bitRateIndexV2L2L3_values = { brFreeV2L2L3, br8V2L2L3, br16V2L2L3, br24V2L2L3, br32V2L2L3, br40V2L2L3, br48V2L2L3, br56V2L2L3, br64V2L2L3, br80V2L2L3, br96V2L2L3, br112V2L2L3, br128V2L2L3, br144V2L2L3, br160V2L2L3 };

typedef enum e_bitRateIndexV2L2L3 E_BITRATEINDEXV2L2L3;
std::vector<uint32> E_BITRATEINDEXV2L2L3_values = { brFreeV2L2L3, br8V2L2L3, br16V2L2L3, br24V2L2L3, br32V2L2L3, br40V2L2L3, br48V2L2L3, br56V2L2L3, br64V2L2L3, br80V2L2L3, br96V2L2L3, br112V2L2L3, br128V2L2L3, br144V2L2L3, br160V2L2L3 };

enum e_samplingRateIndexV1 : uint32 {
	Hz44100 = (uint32) 0,
	Hz48000 = (uint32) 1,
	Hz32000 = (uint32) 2,
};
std::vector<uint32> e_samplingRateIndexV1_values = { Hz44100, Hz48000, Hz32000 };

typedef enum e_samplingRateIndexV1 E_SAMPLINGRATEINDEXV1;
std::vector<uint32> E_SAMPLINGRATEINDEXV1_values = { Hz44100, Hz48000, Hz32000 };

enum e_samplingRateIndexV2 : uint32 {
	Hz22050 = (uint32) 0,
	Hz24000 = (uint32) 1,
	Hz16000 = (uint32) 2,
};
std::vector<uint32> e_samplingRateIndexV2_values = { Hz22050, Hz24000, Hz16000 };

typedef enum e_samplingRateIndexV2 E_SAMPLINGRATEINDEXV2;
std::vector<uint32> E_SAMPLINGRATEINDEXV2_values = { Hz22050, Hz24000, Hz16000 };

enum e_samplingRateIndexV25 : uint32 {
	Hz11025 = (uint32) 0,
	Hz12000 = (uint32) 1,
	Hz8000 = (uint32) 2,
};
std::vector<uint32> e_samplingRateIndexV25_values = { Hz11025, Hz12000, Hz8000 };

typedef enum e_samplingRateIndexV25 E_SAMPLINGRATEINDEXV25;
std::vector<uint32> E_SAMPLINGRATEINDEXV25_values = { Hz11025, Hz12000, Hz8000 };

enum e_paddingBit : uint32 {
	unpadded = (uint32) 0,
	padded = (uint32) 1,
};
std::vector<uint32> e_paddingBit_values = { unpadded, padded };

typedef enum e_paddingBit E_PADDINGBIT;
std::vector<uint32> E_PADDINGBIT_values = { unpadded, padded };

enum e_privateBit : uint32 {
	reserved1 = (uint32) 0,
	reserved2 = (uint32) 1,
};
std::vector<uint32> e_privateBit_values = { reserved1, reserved2 };

typedef enum e_privateBit E_PRIVATEBIT;
std::vector<uint32> E_PRIVATEBIT_values = { reserved1, reserved2 };

enum e_channelMode : uint32 {
	stereo = (uint32) 0,
	joint_stereo = (uint32) 1,
	dual_channel = (uint32) 2,
	single_channel = (uint32) 3,
};
std::vector<uint32> e_channelMode_values = { stereo, joint_stereo, dual_channel, single_channel };

typedef enum e_channelMode E_CHANNELMODE;
std::vector<uint32> E_CHANNELMODE_values = { stereo, joint_stereo, dual_channel, single_channel };

enum e_channelModeSingle : uint32 {
	single_channelSingle = (uint32) 3,
};
std::vector<uint32> e_channelModeSingle_values = { single_channelSingle };

typedef enum e_channelModeSingle E_CHANNELMODESINGLE;
std::vector<uint32> E_CHANNELMODESINGLE_values = { single_channelSingle };

enum e_channelModeNonSingle : uint32 {
	stereoNonSingle = (uint32) 0,
	dual_channelNonSingle = (uint32) 2,
};
std::vector<uint32> e_channelModeNonSingle_values = { stereoNonSingle, dual_channelNonSingle };

typedef enum e_channelModeNonSingle E_CHANNELMODENONSINGLE;
std::vector<uint32> E_CHANNELMODENONSINGLE_values = { stereoNonSingle, dual_channelNonSingle };

enum e_modeExtensionL1L2 : uint32 {
	bands_4to31 = (uint32) 0,
	bands_8to31 = (uint32) 1,
	bands_12to31 = (uint32) 2,
	bands_16to31 = (uint32) 3,
};
std::vector<uint32> e_modeExtensionL1L2_values = { bands_4to31, bands_8to31, bands_12to31, bands_16to31 };

typedef enum e_modeExtensionL1L2 E_MODEEXTENSIONL1L2;
std::vector<uint32> E_MODEEXTENSIONL1L2_values = { bands_4to31, bands_8to31, bands_12to31, bands_16to31 };

enum e_modeExtensionL3 : uint32 {
	noExtension = (uint32) 0,
	intensityStereo = (uint32) 1,
	msStereo = (uint32) 2,
	intensity_msStereo = (uint32) 3,
};
std::vector<uint32> e_modeExtensionL3_values = { noExtension, intensityStereo, msStereo, intensity_msStereo };

typedef enum e_modeExtensionL3 E_MODEEXTENSIONL3;
std::vector<uint32> E_MODEEXTENSIONL3_values = { noExtension, intensityStereo, msStereo, intensity_msStereo };

enum e_copyrightBit : uint32 {
	noCopyright = (uint32) 0,
	copyright = (uint32) 1,
};
std::vector<uint32> e_copyrightBit_values = { noCopyright, copyright };

typedef enum e_copyrightBit E_COPYRIGHTBIT;
std::vector<uint32> E_COPYRIGHTBIT_values = { noCopyright, copyright };

enum e_originalBit : uint32 {
	copy = (uint32) 0,
	original = (uint32) 1,
};
std::vector<uint32> e_originalBit_values = { copy, original };

typedef enum e_originalBit E_ORIGINALBIT;
std::vector<uint32> E_ORIGINALBIT_values = { copy, original };

enum e_emphasis : uint32 {
	none = (uint32) 0,
	ms50to15 = (uint32) 1,
	reserved = (uint32) 2,
	ccitj17 = (uint32) 3,
};
std::vector<uint32> e_emphasis_values = { none, ms50to15, reserved, ccitj17 };

typedef enum e_emphasis E_EMPHASIS;
std::vector<uint32> E_EMPHASIS_values = { none, ms50to15, reserved, ccitj17 };

enum ID3_GENRES : ubyte {
	Blues,
	Classic_Rock,
	Country,
	Dance,
	Disco,
	Funk,
	Grunge,
	Hip_Hop,
	Jazz,
	Metal,
	New_Age,
	Oldies,
	Other,
	Pop,
	R_and_B,
	Rap,
	Reggae,
	Rock,
	Techno,
	Industrial,
	Alternative,
	Ska,
	Death_Metal,
	Pranks,
	Soundtrack,
	Euro_Techno,
	Ambient,
	Trip_Hop,
	Vocal,
	Jazz_Funk,
	Fusion,
	Trance,
	Classical,
	Instrumental,
	Acid,
	House,
	Game,
	Sound_Clip,
	Gospel,
	Noise,
	AlternRock,
	Bass,
	Soul,
	Punk,
	Space,
	Meditative,
	Instrumental_Pop,
	Instrumental_Rock,
	Ethnic,
	Gothic,
	Darkwave,
	Techno_Industrial,
	Electronic,
	Pop_Folk,
	Eurodance,
	Dream,
	Southern_Rock,
	Comedy,
	Cult,
	Gangsta,
	Top_40,
	Christian_Rap,
	Pop_Funk,
	Jungle,
	Native_American,
	Cabaret,
	New_Wave,
	Psychadelic,
	Rave,
	Showtunes,
	Trailer,
	Lo_Fi,
	Tribal,
	Acid_Punk,
	Acid_Jazz,
	Polka,
	Retro,
	Musical,
	Rock_n_Roll,
	Hard_Rock,
	Folk,
	Folk_Rock,
	National_Folk,
	Swing,
	Fast_Fusion,
	Bebob,
	Latin,
	Revival,
	Celtic,
	Bluegrass,
	Avantgarde,
	Gothic_Rock,
	Progressive_Rock,
	Psychedelic_Rock,
	Symphonic_Rock,
	Slow_Rock,
	Big_Band,
	Chorus,
	Easy_Listening,
	Acoustic,
	Humour,
	Speech,
	Chanson,
	Opera,
	Chamber_Music,
	Sonata,
	Symphony,
	Booty_Bass,
	Primus,
	Porn_Groove,
	Satire,
	Slow_Jam,
	Club,
	Tango,
	Samba,
	Folklore,
	Ballad,
	Power_Ballad,
	Rhythmic_Soul,
	Freestyle,
	Duet,
	Punk_Rock,
	Drum_Solo,
	A_capella,
	Euro_House,
	Dance_Hall,
	Goa,
	Drum_and_Bass,
	Club_House,
	Hardcore,
	Terror,
	Indie,
	BritPop,
	Negerpunk,
	Polsk_Punk,
	Beat,
	Christian,
	Heavy_Metal,
	Black_Metal,
	Crossover,
	Contemporary,
	Christian_Rock,
	Merengue,
	Salsa,
	Thrash_Metal,
	Anime,
	JPop,
	Synthpop,
};
std::vector<ubyte> ID3_GENRES_values = { Blues, Classic_Rock, Country, Dance, Disco, Funk, Grunge, Hip_Hop, Jazz, Metal, New_Age, Oldies, Other, Pop, R_and_B, Rap, Reggae, Rock, Techno, Industrial, Alternative, Ska, Death_Metal, Pranks, Soundtrack, Euro_Techno, Ambient, Trip_Hop, Vocal, Jazz_Funk, Fusion, Trance, Classical, Instrumental, Acid, House, Game, Sound_Clip, Gospel, Noise, AlternRock, Bass, Soul, Punk, Space, Meditative, Instrumental_Pop, Instrumental_Rock, Ethnic, Gothic, Darkwave, Techno_Industrial, Electronic, Pop_Folk, Eurodance, Dream, Southern_Rock, Comedy, Cult, Gangsta, Top_40, Christian_Rap, Pop_Funk, Jungle, Native_American, Cabaret, New_Wave, Psychadelic, Rave, Showtunes, Trailer, Lo_Fi, Tribal, Acid_Punk, Acid_Jazz, Polka, Retro, Musical, Rock_n_Roll, Hard_Rock, Folk, Folk_Rock, National_Folk, Swing, Fast_Fusion, Bebob, Latin, Revival, Celtic, Bluegrass, Avantgarde, Gothic_Rock, Progressive_Rock, Psychedelic_Rock, Symphonic_Rock, Slow_Rock, Big_Band, Chorus, Easy_Listening, Acoustic, Humour, Speech, Chanson, Opera, Chamber_Music, Sonata, Symphony, Booty_Bass, Primus, Porn_Groove, Satire, Slow_Jam, Club, Tango, Samba, Folklore, Ballad, Power_Ballad, Rhythmic_Soul, Freestyle, Duet, Punk_Rock, Drum_Solo, A_capella, Euro_House, Dance_Hall, Goa, Drum_and_Bass, Club_House, Hardcore, Terror, Indie, BritPop, Negerpunk, Polsk_Punk, Beat, Christian, Heavy_Metal, Black_Metal, Crossover, Contemporary, Christian_Rock, Merengue, Salsa, Thrash_Metal, Anime, JPop, Synthpop };


class char_class {
	int small;
	std::vector<char> known_values;
	char value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(char);
	char operator () () { return value; }
	char_class(int small, std::vector<char> known_values = {}) : small(small), known_values(known_values) {}

	char generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(char), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(char), 0, known_values);
		}
		return value;
	}

	char generate(std::vector<char> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(char), 0, possible_values);
		return value;
	}
};



class char_array_class {
	char_class& element;
	std::vector<std::string> known_values;
	std::unordered_map<int, std::vector<char>> element_known_values;
	std::string value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::string& operator () () { return value; }
	char operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	char_array_class(char_class& element, std::unordered_map<int, std::vector<char>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}
	char_array_class(char_class& element, std::vector<std::string> known_values)
		: element(element), known_values(known_values) {}

	std::string generate(unsigned size, std::vector<std::string> possible_values = {}) {
		check_array_length(size);
		_startof = FTell();
		value = "";
		if (possible_values.size()) {
			value = file_acc.file_string(possible_values);
			assert(value.length() == size);
			_sizeof = size;
			return value;
		}
		if (known_values.size()) {
			value = file_acc.file_string(known_values);
			assert(value.length() == size);
			_sizeof = size;
			return value;
		}
		if (!element_known_values.size()) {
			if (size == 0)
				 return "";
			value = file_acc.file_string(size);
			_sizeof = size;
			return value;
		}
		for (unsigned i = 0; i < size; ++i) {
			auto known = element_known_values.find(i);
			if (known == element_known_values.end()) {
				value.push_back(element.generate());
				_sizeof += element._sizeof;
			} else {
				value.push_back(file_acc.file_integer(sizeof(char), 0, known->second));
				_sizeof += sizeof(char);
			}
		}
		return value;
	}
};



class ubyte_class {
	int small;
	std::vector<ubyte> known_values;
	ubyte value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(ubyte);
	ubyte operator () () { return value; }
	ubyte_class(int small, std::vector<ubyte> known_values = {}) : small(small), known_values(known_values) {}

	ubyte generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(ubyte), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(ubyte), 0, known_values);
		}
		return value;
	}

	ubyte generate(std::vector<ubyte> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(ubyte), 0, possible_values);
		return value;
	}
};



class FLAGS {
	std::vector<FLAGS*>& instances;

	ubyte i_unsyn_used_var;
	ubyte i_extend_head_pres_var;
	ubyte i_experiment_tag_var;
	ubyte reserv_flags_var;
	ubyte flags_var;

public:
	bool i_unsyn_used_exists = false;
	bool i_extend_head_pres_exists = false;
	bool i_experiment_tag_exists = false;
	bool reserv_flags_exists = false;
	bool flags_exists = false;

	ubyte& i_unsyn_used() {
		assert_cond(i_unsyn_used_exists, "struct field i_unsyn_used does not exist");
		return i_unsyn_used_var;
	}
	ubyte& i_extend_head_pres() {
		assert_cond(i_extend_head_pres_exists, "struct field i_extend_head_pres does not exist");
		return i_extend_head_pres_var;
	}
	ubyte& i_experiment_tag() {
		assert_cond(i_experiment_tag_exists, "struct field i_experiment_tag does not exist");
		return i_experiment_tag_var;
	}
	ubyte& reserv_flags() {
		assert_cond(reserv_flags_exists, "struct field reserv_flags does not exist");
		return reserv_flags_var;
	}
	ubyte& flags() {
		assert_cond(flags_exists, "struct field flags does not exist");
		return flags_var;
	}

	/* locals */
	int current_pos;
	ubyte full_flags;
	ubyte unsyn_used;
	ubyte extend_head_pres;
	ubyte experiment_tag;
	ubyte UNSYNCHRONISATION_USED;
	ubyte EXTENDED_HEADER_PRESENT;
	ubyte EXPERIMENTAL_TAG;
	ubyte RESERVED_FLAGS;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	FLAGS& operator () () { return *instances.back(); }
	FLAGS& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	FLAGS(std::vector<FLAGS*>& instances) : instances(instances) { instances.push_back(this); }
	~FLAGS() {
		if (generated == 2)
			return;
		while (instances.size()) {
			FLAGS* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	FLAGS* generate();
};

int FLAGS::_parent_id = 0;
int FLAGS::_index_start = 0;



class ID3v2_HEADER {
	std::vector<ID3v2_HEADER*>& instances;

	std::string head_var;
	char ver_major_var;
	char ver_revision_var;
	FLAGS* flags_var;

public:
	bool head_exists = false;
	bool ver_major_exists = false;
	bool ver_revision_exists = false;
	bool flags_exists = false;

	std::string& head() {
		assert_cond(head_exists, "struct field head does not exist");
		return head_var;
	}
	char& ver_major() {
		assert_cond(ver_major_exists, "struct field ver_major does not exist");
		return ver_major_var;
	}
	char& ver_revision() {
		assert_cond(ver_revision_exists, "struct field ver_revision does not exist");
		return ver_revision_var;
	}
	FLAGS& flags() {
		assert_cond(flags_exists, "struct field flags does not exist");
		return *flags_var;
	}

	/* locals */
	uint32 size;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	ID3v2_HEADER& operator () () { return *instances.back(); }
	ID3v2_HEADER& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	ID3v2_HEADER(std::vector<ID3v2_HEADER*>& instances) : instances(instances) { instances.push_back(this); }
	~ID3v2_HEADER() {
		if (generated == 2)
			return;
		while (instances.size()) {
			ID3v2_HEADER* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	ID3v2_HEADER* generate();
};

int ID3v2_HEADER::_parent_id = 0;
int ID3v2_HEADER::_index_start = 0;



class ubyte_array_class {
	ubyte_class& element;
	std::unordered_map<int, std::vector<ubyte>> element_known_values;
	std::vector<ubyte> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<ubyte>& operator () () { return value; }
	ubyte operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	ubyte_array_class(ubyte_class& element, std::unordered_map<int, std::vector<ubyte>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}

	std::vector<ubyte> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			auto known = element_known_values.find(i);
			if (known == element_known_values.end()) {
				value.push_back(element.generate());
				_sizeof += element._sizeof;
			} else {
				value.push_back(file_acc.file_integer(sizeof(ubyte), 0, known->second));
				_sizeof += sizeof(ubyte);
			}
		}
		return value;
	}
};



class uint32_class {
	int small;
	std::vector<uint32> known_values;
	uint32 value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(uint32);
	uint32 operator () () { return value; }
	uint32_class(int small, std::vector<uint32> known_values = {}) : small(small), known_values(known_values) {}

	uint32 generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(uint32), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(uint32), 0, known_values);
		}
		return value;
	}

	uint32 generate(std::vector<uint32> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(uint32), 0, possible_values);
		return value;
	}
};



class uint16_bitfield {
	int small;
	std::vector<uint16> known_values;
	uint16 value;
public:
	uint16 operator () () { return value; }
	uint16_bitfield(int small, std::vector<uint16> known_values = {}) : small(small), known_values(known_values) {}

	uint16 generate(unsigned bits) {
		if (!bits)
			return 0;
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(uint16), bits, small);
		} else {
			value = file_acc.file_integer(sizeof(uint16), bits, known_values);
		}
		return value;
	}

	uint16 generate(unsigned bits, std::vector<uint16> possible_values) {
		if (!bits)
			return 0;
		value = file_acc.file_integer(sizeof(uint16), bits, possible_values);
		return value;
	}
};



class ID3v2_EXTENDED_HEADER {
	std::vector<ID3v2_EXTENDED_HEADER*>& instances;

	uint32 size_var;
	uint16 FLAG_CRC_PRESENT_var : 1;
	uint16 uint16_bitfield_padding_var : 15;
	uint32 padding_sz_var;
	uint32 crc_var;

public:
	bool size_exists = false;
	bool FLAG_CRC_PRESENT_exists = false;
	bool uint16_bitfield_padding_exists = false;
	bool padding_sz_exists = false;
	bool crc_exists = false;

	uint32& size() {
		assert_cond(size_exists, "struct field size does not exist");
		return size_var;
	}
	uint16 FLAG_CRC_PRESENT() {
		assert_cond(FLAG_CRC_PRESENT_exists, "struct field FLAG_CRC_PRESENT does not exist");
		return FLAG_CRC_PRESENT_var;
	}
	uint16 uint16_bitfield_padding() {
		assert_cond(uint16_bitfield_padding_exists, "struct field uint16_bitfield_padding does not exist");
		return uint16_bitfield_padding_var;
	}
	uint32& padding_sz() {
		assert_cond(padding_sz_exists, "struct field padding_sz does not exist");
		return padding_sz_var;
	}
	uint32& crc() {
		assert_cond(crc_exists, "struct field crc does not exist");
		return crc_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	ID3v2_EXTENDED_HEADER& operator () () { return *instances.back(); }
	ID3v2_EXTENDED_HEADER& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	ID3v2_EXTENDED_HEADER(std::vector<ID3v2_EXTENDED_HEADER*>& instances) : instances(instances) { instances.push_back(this); }
	~ID3v2_EXTENDED_HEADER() {
		if (generated == 2)
			return;
		while (instances.size()) {
			ID3v2_EXTENDED_HEADER* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	ID3v2_EXTENDED_HEADER* generate();
};

int ID3v2_EXTENDED_HEADER::_parent_id = 0;
int ID3v2_EXTENDED_HEADER::_index_start = 0;



class FRAME_FLAGS {
	std::vector<FRAME_FLAGS*>& instances;

	uint16 TAG_ALTER_PRESERV_var : 1;
	uint16 FILE_ALTER_PRESERV_var : 1;
	uint16 READ_ONLY_FRAME_var : 1;
	uint16 uint16_bitfield_padding_var : 5;
	uint16 COMPRESSED_FRAME_var : 1;
	uint16 ENCRYPTED_FRAME_var : 1;
	uint16 GROUP_MEMBER_FRAME_var : 1;

public:
	bool TAG_ALTER_PRESERV_exists = false;
	bool FILE_ALTER_PRESERV_exists = false;
	bool READ_ONLY_FRAME_exists = false;
	bool uint16_bitfield_padding_exists = false;
	bool COMPRESSED_FRAME_exists = false;
	bool ENCRYPTED_FRAME_exists = false;
	bool GROUP_MEMBER_FRAME_exists = false;

	uint16 TAG_ALTER_PRESERV() {
		assert_cond(TAG_ALTER_PRESERV_exists, "struct field TAG_ALTER_PRESERV does not exist");
		return TAG_ALTER_PRESERV_var;
	}
	uint16 FILE_ALTER_PRESERV() {
		assert_cond(FILE_ALTER_PRESERV_exists, "struct field FILE_ALTER_PRESERV does not exist");
		return FILE_ALTER_PRESERV_var;
	}
	uint16 READ_ONLY_FRAME() {
		assert_cond(READ_ONLY_FRAME_exists, "struct field READ_ONLY_FRAME does not exist");
		return READ_ONLY_FRAME_var;
	}
	uint16 uint16_bitfield_padding() {
		assert_cond(uint16_bitfield_padding_exists, "struct field uint16_bitfield_padding does not exist");
		return uint16_bitfield_padding_var;
	}
	uint16 COMPRESSED_FRAME() {
		assert_cond(COMPRESSED_FRAME_exists, "struct field COMPRESSED_FRAME does not exist");
		return COMPRESSED_FRAME_var;
	}
	uint16 ENCRYPTED_FRAME() {
		assert_cond(ENCRYPTED_FRAME_exists, "struct field ENCRYPTED_FRAME does not exist");
		return ENCRYPTED_FRAME_var;
	}
	uint16 GROUP_MEMBER_FRAME() {
		assert_cond(GROUP_MEMBER_FRAME_exists, "struct field GROUP_MEMBER_FRAME does not exist");
		return GROUP_MEMBER_FRAME_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	FRAME_FLAGS& operator () () { return *instances.back(); }
	FRAME_FLAGS& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	FRAME_FLAGS(std::vector<FRAME_FLAGS*>& instances) : instances(instances) { instances.push_back(this); }
	~FRAME_FLAGS() {
		if (generated == 2)
			return;
		while (instances.size()) {
			FRAME_FLAGS* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	FRAME_FLAGS* generate();
};

int FRAME_FLAGS::_parent_id = 0;
int FRAME_FLAGS::_index_start = 0;



class byte_class {
	int small;
	std::vector<byte> known_values;
	byte value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(byte);
	byte operator () () { return value; }
	byte_class(int small, std::vector<byte> known_values = {}) : small(small), known_values(known_values) {}

	byte generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(byte), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(byte), 0, known_values);
		}
		return value;
	}

	byte generate(std::vector<byte> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(byte), 0, possible_values);
		return value;
	}
};



class ID3v2_FRAME {
	std::vector<ID3v2_FRAME*>& instances;

	std::string id_var;
	uint32 size_var;
	FRAME_FLAGS* flags_var;
	byte id_asciiz_str_var;

public:
	bool id_exists = false;
	bool size_exists = false;
	bool flags_exists = false;
	bool id_asciiz_str_exists = false;

	std::string& id() {
		assert_cond(id_exists, "struct field id does not exist");
		return id_var;
	}
	uint32& size() {
		assert_cond(size_exists, "struct field size does not exist");
		return size_var;
	}
	FRAME_FLAGS& flags() {
		assert_cond(flags_exists, "struct field flags does not exist");
		return *flags_var;
	}
	byte& id_asciiz_str() {
		assert_cond(id_asciiz_str_exists, "struct field id_asciiz_str does not exist");
		return id_asciiz_str_var;
	}

	/* locals */
	int id3v2_frame_size_location;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	ID3v2_FRAME& operator () () { return *instances.back(); }
	ID3v2_FRAME& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	ID3v2_FRAME(std::vector<ID3v2_FRAME*>& instances) : instances(instances) { instances.push_back(this); }
	~ID3v2_FRAME() {
		if (generated == 2)
			return;
		while (instances.size()) {
			ID3v2_FRAME* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	ID3v2_FRAME* generate();
};

int ID3v2_FRAME::_parent_id = 0;
int ID3v2_FRAME::_index_start = 0;


enum encoding_enum : ubyte {
	ISO_8859_1,
	UTF_16_with_BOM,
	UTF_16BE_without_BOM,
	UTF_8,
};
std::vector<ubyte> encoding_enum_values = { ISO_8859_1, UTF_16_with_BOM, UTF_16BE_without_BOM, UTF_8 };

encoding_enum encoding_enum_generate() {
	return (encoding_enum) file_acc.file_integer(sizeof(ubyte), 0, encoding_enum_values);
}

encoding_enum encoding_enum_generate(std::vector<ubyte> known_values) {
	return (encoding_enum) file_acc.file_integer(sizeof(ubyte), 0, known_values);
}


class ID3v2_4_FRAME {
	std::vector<ID3v2_4_FRAME*>& instances;

	std::string id_var;
	uint32 size_var;
	FRAME_FLAGS* flags_var;
	ubyte encoding_var;

public:
	bool id_exists = false;
	bool size_exists = false;
	bool flags_exists = false;
	bool encoding_exists = false;

	std::string& id() {
		assert_cond(id_exists, "struct field id does not exist");
		return id_var;
	}
	uint32& size() {
		assert_cond(size_exists, "struct field size does not exist");
		return size_var;
	}
	FRAME_FLAGS& flags() {
		assert_cond(flags_exists, "struct field flags does not exist");
		return *flags_var;
	}
	ubyte& encoding() {
		assert_cond(encoding_exists, "struct field encoding does not exist");
		return encoding_var;
	}

	/* locals */
	int id3v2_4_synchsafe_pos;
	int id3v2_4_frame_start_no_header;
	int id3v2_4_frame_end;
	int id3v2_4_frame_size;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	ID3v2_4_FRAME& operator () () { return *instances.back(); }
	ID3v2_4_FRAME& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	ID3v2_4_FRAME(std::vector<ID3v2_4_FRAME*>& instances) : instances(instances) { instances.push_back(this); }
	~ID3v2_4_FRAME() {
		if (generated == 2)
			return;
		while (instances.size()) {
			ID3v2_4_FRAME* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	ID3v2_4_FRAME* generate();
};

int ID3v2_4_FRAME::_parent_id = 0;
int ID3v2_4_FRAME::_index_start = 0;



class ID3v2_TAG {
	std::vector<ID3v2_TAG*>& instances;

	ID3v2_HEADER* hdr_var;
	std::vector<ubyte> id3v2_data_var;
	ID3v2_EXTENDED_HEADER* ext_hdr_var;
	std::vector<ubyte> id3v2_padding_var;

public:
	bool hdr_exists = false;
	bool id3v2_data_exists = false;
	bool ext_hdr_exists = false;
	bool id3v2_padding_exists = false;

	ID3v2_HEADER& hdr() {
		assert_cond(hdr_exists, "struct field hdr does not exist");
		return *hdr_var;
	}
	std::vector<ubyte>& id3v2_data() {
		assert_cond(id3v2_data_exists, "struct field id3v2_data does not exist");
		return id3v2_data_var;
	}
	ID3v2_EXTENDED_HEADER& ext_hdr() {
		assert_cond(ext_hdr_exists, "struct field ext_hdr does not exist");
		return *ext_hdr_var;
	}
	std::vector<ubyte>& id3v2_padding() {
		assert_cond(id3v2_padding_exists, "struct field id3v2_padding does not exist");
		return id3v2_padding_var;
	}

	/* locals */
	uint32 tag_sz;
	uint32 frame_color;
	uint32 id3v2_tag_full_size;
	uint32 size;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	ID3v2_TAG& operator () () { return *instances.back(); }
	ID3v2_TAG& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	ID3v2_TAG(std::vector<ID3v2_TAG*>& instances) : instances(instances) { instances.push_back(this); }
	~ID3v2_TAG() {
		if (generated == 2)
			return;
		while (instances.size()) {
			ID3v2_TAG* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	ID3v2_TAG* generate();
};

int ID3v2_TAG::_parent_id = 0;
int ID3v2_TAG::_index_start = 0;


e_mpegVersion e_mpegVersion_generate() {
	return (e_mpegVersion) file_acc.file_integer(sizeof(uint32), 0, e_mpegVersion_values);
}

e_mpegVersion e_mpegVersion_generate(std::vector<uint32> known_values) {
	return (e_mpegVersion) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_layerVersion e_layerVersion_generate() {
	return (e_layerVersion) file_acc.file_integer(sizeof(uint32), 0, e_layerVersion_values);
}

e_layerVersion e_layerVersion_generate(std::vector<uint32> known_values) {
	return (e_layerVersion) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_protectionBit e_protectionBit_generate() {
	return (e_protectionBit) file_acc.file_integer(sizeof(uint32), 0, e_protectionBit_values);
}

e_protectionBit e_protectionBit_generate(std::vector<uint32> known_values) {
	return (e_protectionBit) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_bitRateIndexV2L2L3 e_bitRateIndexV2L2L3_generate() {
	return (e_bitRateIndexV2L2L3) file_acc.file_integer(sizeof(uint32), 0, e_bitRateIndexV2L2L3_values);
}

e_bitRateIndexV2L2L3 e_bitRateIndexV2L2L3_generate(std::vector<uint32> known_values) {
	return (e_bitRateIndexV2L2L3) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_bitRateIndexV2L1 e_bitRateIndexV2L1_generate() {
	return (e_bitRateIndexV2L1) file_acc.file_integer(sizeof(uint32), 0, e_bitRateIndexV2L1_values);
}

e_bitRateIndexV2L1 e_bitRateIndexV2L1_generate(std::vector<uint32> known_values) {
	return (e_bitRateIndexV2L1) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_bitRateIndexV1L3 e_bitRateIndexV1L3_generate() {
	return (e_bitRateIndexV1L3) file_acc.file_integer(sizeof(uint32), 0, e_bitRateIndexV1L3_values);
}

e_bitRateIndexV1L3 e_bitRateIndexV1L3_generate(std::vector<uint32> known_values) {
	return (e_bitRateIndexV1L3) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_bitRateIndexV1L2 e_bitRateIndexV1L2_generate() {
	return (e_bitRateIndexV1L2) file_acc.file_integer(sizeof(uint32), 0, e_bitRateIndexV1L2_values);
}

e_bitRateIndexV1L2 e_bitRateIndexV1L2_generate(std::vector<uint32> known_values) {
	return (e_bitRateIndexV1L2) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_bitRateIndexV1L1 e_bitRateIndexV1L1_generate() {
	return (e_bitRateIndexV1L1) file_acc.file_integer(sizeof(uint32), 0, e_bitRateIndexV1L1_values);
}

e_bitRateIndexV1L1 e_bitRateIndexV1L1_generate(std::vector<uint32> known_values) {
	return (e_bitRateIndexV1L1) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_samplingRateIndexV25 e_samplingRateIndexV25_generate() {
	return (e_samplingRateIndexV25) file_acc.file_integer(sizeof(uint32), 0, e_samplingRateIndexV25_values);
}

e_samplingRateIndexV25 e_samplingRateIndexV25_generate(std::vector<uint32> known_values) {
	return (e_samplingRateIndexV25) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_samplingRateIndexV2 e_samplingRateIndexV2_generate() {
	return (e_samplingRateIndexV2) file_acc.file_integer(sizeof(uint32), 0, e_samplingRateIndexV2_values);
}

e_samplingRateIndexV2 e_samplingRateIndexV2_generate(std::vector<uint32> known_values) {
	return (e_samplingRateIndexV2) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_samplingRateIndexV1 e_samplingRateIndexV1_generate() {
	return (e_samplingRateIndexV1) file_acc.file_integer(sizeof(uint32), 0, e_samplingRateIndexV1_values);
}

e_samplingRateIndexV1 e_samplingRateIndexV1_generate(std::vector<uint32> known_values) {
	return (e_samplingRateIndexV1) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_paddingBit e_paddingBit_generate() {
	return (e_paddingBit) file_acc.file_integer(sizeof(uint32), 0, e_paddingBit_values);
}

e_paddingBit e_paddingBit_generate(std::vector<uint32> known_values) {
	return (e_paddingBit) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_privateBit e_privateBit_generate() {
	return (e_privateBit) file_acc.file_integer(sizeof(uint32), 0, e_privateBit_values);
}

e_privateBit e_privateBit_generate(std::vector<uint32> known_values) {
	return (e_privateBit) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_channelMode e_channelMode_generate() {
	return (e_channelMode) file_acc.file_integer(sizeof(uint32), 0, e_channelMode_values);
}

e_channelMode e_channelMode_generate(std::vector<uint32> known_values) {
	return (e_channelMode) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_channelModeSingle e_channelModeSingle_generate() {
	return (e_channelModeSingle) file_acc.file_integer(sizeof(uint32), 0, e_channelModeSingle_values);
}

e_channelModeSingle e_channelModeSingle_generate(std::vector<uint32> known_values) {
	return (e_channelModeSingle) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_channelModeNonSingle e_channelModeNonSingle_generate() {
	return (e_channelModeNonSingle) file_acc.file_integer(sizeof(uint32), 0, e_channelModeNonSingle_values);
}

e_channelModeNonSingle e_channelModeNonSingle_generate(std::vector<uint32> known_values) {
	return (e_channelModeNonSingle) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_modeExtensionL1L2 e_modeExtensionL1L2_generate() {
	return (e_modeExtensionL1L2) file_acc.file_integer(sizeof(uint32), 0, e_modeExtensionL1L2_values);
}

e_modeExtensionL1L2 e_modeExtensionL1L2_generate(std::vector<uint32> known_values) {
	return (e_modeExtensionL1L2) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_copyrightBit e_copyrightBit_generate() {
	return (e_copyrightBit) file_acc.file_integer(sizeof(uint32), 0, e_copyrightBit_values);
}

e_copyrightBit e_copyrightBit_generate(std::vector<uint32> known_values) {
	return (e_copyrightBit) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_originalBit e_originalBit_generate() {
	return (e_originalBit) file_acc.file_integer(sizeof(uint32), 0, e_originalBit_values);
}

e_originalBit e_originalBit_generate(std::vector<uint32> known_values) {
	return (e_originalBit) file_acc.file_integer(sizeof(uint32), 0, known_values);
}

e_emphasis e_emphasis_generate() {
	return (e_emphasis) file_acc.file_integer(sizeof(uint32), 0, e_emphasis_values);
}

e_emphasis e_emphasis_generate(std::vector<uint32> known_values) {
	return (e_emphasis) file_acc.file_integer(sizeof(uint32), 0, known_values);
}


class uint16_class {
	int small;
	std::vector<uint16> known_values;
	uint16 value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(uint16);
	uint16 operator () () { return value; }
	uint16_class(int small, std::vector<uint16> known_values = {}) : small(small), known_values(known_values) {}

	uint16 generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(uint16), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(uint16), 0, known_values);
		}
		return value;
	}

	uint16 generate(std::vector<uint16> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(uint16), 0, possible_values);
		return value;
	}
};



class MPEG_HEADER {
	std::vector<MPEG_HEADER*>& instances;

	uint32 input1_var;
	uint32 input2_var;
	uint32 input3_var;
	uint32 input4_var;
	uint32 input5_var;
	uint32 input6_var;
	uint32 input7_var;
	uint32 input8_var;
	uint32 input9_var;
	uint32 input10_var;
	uint32 input11_var;
	uint32 input12_var;
	uint32 full_hdr_var;
	uint16 crc16_var;

public:
	bool input1_exists = false;
	bool input2_exists = false;
	bool input3_exists = false;
	bool input4_exists = false;
	bool input5_exists = false;
	bool input6_exists = false;
	bool input7_exists = false;
	bool input8_exists = false;
	bool input9_exists = false;
	bool input10_exists = false;
	bool input11_exists = false;
	bool input12_exists = false;
	bool full_hdr_exists = false;
	bool crc16_exists = false;

	uint32& input1() {
		assert_cond(input1_exists, "struct field input1 does not exist");
		return input1_var;
	}
	uint32& input2() {
		assert_cond(input2_exists, "struct field input2 does not exist");
		return input2_var;
	}
	uint32& input3() {
		assert_cond(input3_exists, "struct field input3 does not exist");
		return input3_var;
	}
	uint32& input4() {
		assert_cond(input4_exists, "struct field input4 does not exist");
		return input4_var;
	}
	uint32& input5() {
		assert_cond(input5_exists, "struct field input5 does not exist");
		return input5_var;
	}
	uint32& input6() {
		assert_cond(input6_exists, "struct field input6 does not exist");
		return input6_var;
	}
	uint32& input7() {
		assert_cond(input7_exists, "struct field input7 does not exist");
		return input7_var;
	}
	uint32& input8() {
		assert_cond(input8_exists, "struct field input8 does not exist");
		return input8_var;
	}
	uint32& input9() {
		assert_cond(input9_exists, "struct field input9 does not exist");
		return input9_var;
	}
	uint32& input10() {
		assert_cond(input10_exists, "struct field input10 does not exist");
		return input10_var;
	}
	uint32& input11() {
		assert_cond(input11_exists, "struct field input11 does not exist");
		return input11_var;
	}
	uint32& input12() {
		assert_cond(input12_exists, "struct field input12 does not exist");
		return input12_var;
	}
	uint32& full_hdr() {
		assert_cond(full_hdr_exists, "struct field full_hdr does not exist");
		return full_hdr_var;
	}
	uint16& crc16() {
		assert_cond(crc16_exists, "struct field crc16 does not exist");
		return crc16_var;
	}

	/* locals */
	uint64 mpeg_header_start;
	int current_pos;
	uint32 full_input;
	uint32 frame_sync;
	uint32 mpeg_id;
	uint32 layer_id;
	uint32 protection_bit;
	uint32 bitrate_index;
	uint32 frequency_index;
	uint32 padding_bit;
	uint32 private_bit;
	uint32 channel_mode;
	uint32 mode_extension;
	uint32 copyright;
	uint32 original;
	uint32 emphasis;
	uint64 mpeg_header_end;
	uint64 mpeg_header_size;
	uint16 crc_calc;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	MPEG_HEADER& operator () () { return *instances.back(); }
	MPEG_HEADER& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	MPEG_HEADER(std::vector<MPEG_HEADER*>& instances) : instances(instances) { instances.push_back(this); }
	~MPEG_HEADER() {
		if (generated == 2)
			return;
		while (instances.size()) {
			MPEG_HEADER* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	MPEG_HEADER* generate();
};

int MPEG_HEADER::_parent_id = 0;
int MPEG_HEADER::_index_start = 0;



class MPEG_FRAME {
	std::vector<MPEG_FRAME*>& instances;

	MPEG_HEADER* mpeg_hdr_var;
	std::vector<ubyte> mpeg_frame_data_var;

public:
	bool mpeg_hdr_exists = false;
	bool mpeg_frame_data_exists = false;

	MPEG_HEADER& mpeg_hdr() {
		assert_cond(mpeg_hdr_exists, "struct field mpeg_hdr does not exist");
		return *mpeg_hdr_var;
	}
	std::vector<ubyte>& mpeg_frame_data() {
		assert_cond(mpeg_frame_data_exists, "struct field mpeg_frame_data does not exist");
		return mpeg_frame_data_var;
	}

	/* locals */
	uint16 fr0;
	uint16 fr1;
	uint16 fr2;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	MPEG_FRAME& operator () () { return *instances.back(); }
	MPEG_FRAME& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	MPEG_FRAME(std::vector<MPEG_FRAME*>& instances) : instances(instances) { instances.push_back(this); }
	~MPEG_FRAME() {
		if (generated == 2)
			return;
		while (instances.size()) {
			MPEG_FRAME* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	MPEG_FRAME* generate();
};

int MPEG_FRAME::_parent_id = 0;
int MPEG_FRAME::_index_start = 0;


ID3_GENRES ID3_GENRES_generate() {
	return (ID3_GENRES) file_acc.file_integer(sizeof(ubyte), 0, ID3_GENRES_values);
}

ID3_GENRES ID3_GENRES_generate(std::vector<ubyte> known_values) {
	return (ID3_GENRES) file_acc.file_integer(sizeof(ubyte), 0, known_values);
}


class ID3v1_TAG {
	std::vector<ID3v1_TAG*>& instances;

	std::string id_var;
	std::string title_var;
	std::string artist_var;
	std::string album_var;
	std::string year_var;
	std::string comment_var;
	byte zero_var;
	ubyte track_var;
	ubyte genre_var;

public:
	bool id_exists = false;
	bool title_exists = false;
	bool artist_exists = false;
	bool album_exists = false;
	bool year_exists = false;
	bool comment_exists = false;
	bool zero_exists = false;
	bool track_exists = false;
	bool genre_exists = false;

	std::string& id() {
		assert_cond(id_exists, "struct field id does not exist");
		return id_var;
	}
	std::string& title() {
		assert_cond(title_exists, "struct field title does not exist");
		return title_var;
	}
	std::string& artist() {
		assert_cond(artist_exists, "struct field artist does not exist");
		return artist_var;
	}
	std::string& album() {
		assert_cond(album_exists, "struct field album does not exist");
		return album_var;
	}
	std::string& year() {
		assert_cond(year_exists, "struct field year does not exist");
		return year_var;
	}
	std::string& comment() {
		assert_cond(comment_exists, "struct field comment does not exist");
		return comment_var;
	}
	byte& zero() {
		assert_cond(zero_exists, "struct field zero does not exist");
		return zero_var;
	}
	ubyte& track() {
		assert_cond(track_exists, "struct field track does not exist");
		return track_var;
	}
	ubyte& genre() {
		assert_cond(genre_exists, "struct field genre does not exist");
		return genre_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	ID3v1_TAG& operator () () { return *instances.back(); }
	ID3v1_TAG& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	ID3v1_TAG(std::vector<ID3v1_TAG*>& instances) : instances(instances) { instances.push_back(this); }
	~ID3v1_TAG() {
		if (generated == 2)
			return;
		while (instances.size()) {
			ID3v1_TAG* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	ID3v1_TAG* generate();
};

int ID3v1_TAG::_parent_id = 0;
int ID3v1_TAG::_index_start = 0;

std::vector<byte> ReadByteInitValues = { 0, 1 };
std::vector<ubyte> ReadUByteInitValues = { 0x47 };
std::vector<short> ReadShortInitValues;
std::vector<ushort> ReadUShortInitValues;
std::vector<int> ReadIntInitValues;
std::vector<uint> ReadUIntInitValues;
std::vector<int64> ReadQuadInitValues;
std::vector<uint64> ReadUQuadInitValues;
std::vector<int64> ReadInt64InitValues;
std::vector<uint64> ReadUInt64InitValues;
std::vector<hfloat> ReadHFloatInitValues;
std::vector<float> ReadFloatInitValues;
std::vector<double> ReadDoubleInitValues;
std::vector<std::string> ReadBytesInitValues;


std::vector<FLAGS*> FLAGS_flags__instances;
std::vector<ID3v2_HEADER*> ID3v2_HEADER_hdr_instances;
std::vector<ID3v2_EXTENDED_HEADER*> ID3v2_EXTENDED_HEADER_ext_hdr_instances;
std::vector<FRAME_FLAGS*> FRAME_FLAGS_flags___instances;
std::vector<ID3v2_FRAME*> ID3v2_FRAME_tf_instances;
std::vector<ID3v2_4_FRAME*> ID3v2_4_FRAME_tf__instances;
std::vector<ID3v2_TAG*> ID3v2_TAG_id3v2_tag_instances;
std::vector<MPEG_HEADER*> MPEG_HEADER_mpeg_hdr_instances;
std::vector<MPEG_FRAME*> MPEG_FRAME_mf_instances;
std::vector<ID3v1_TAG*> ID3v1_TAG_id3v1_tag_instances;


std::unordered_map<std::string, std::string> variable_types = { { "head", "char_array_class" }, { "ver_major", "char_class" }, { "ver_revision", "char_class" }, { "i_unsyn_used", "ubyte_class" }, { "i_extend_head_pres", "ubyte_class" }, { "i_experiment_tag", "ubyte_class" }, { "reserv_flags", "ubyte_class" }, { "flags", "ubyte_class" }, { "flags_", "FLAGS" }, { "first", "ubyte_class" }, { "second", "ubyte_class" }, { "third", "ubyte_class" }, { "fourth", "ubyte_class" }, { "hdr", "ID3v2_HEADER" }, { "id3v2_data", "ubyte_array_class" }, { "size", "uint32_class" }, { "FLAG_CRC_PRESENT", "uint16_bitfield" }, { "uint16_bitfield_padding", "uint16_bitfield" }, { "padding_sz", "uint32_class" }, { "crc", "uint32_class" }, { "ext_hdr", "ID3v2_EXTENDED_HEADER" }, { "id", "char_array_class" }, { "TAG_ALTER_PRESERV", "uint16_bitfield" }, { "FILE_ALTER_PRESERV", "uint16_bitfield" }, { "READ_ONLY_FRAME", "uint16_bitfield" }, { "COMPRESSED_FRAME", "uint16_bitfield" }, { "ENCRYPTED_FRAME", "uint16_bitfield" }, { "GROUP_MEMBER_FRAME", "uint16_bitfield" }, { "flags__", "FRAME_FLAGS" }, { "id_asciiz_str", "byte_class" }, { "frame_data", "char_array_class" }, { "frame_data_", "ubyte_array_class" }, { "tf", "ID3v2_FRAME" }, { "encoding", "encoding_enum" }, { "tf_", "ID3v2_4_FRAME" }, { "id3v2_padding", "ubyte_array_class" }, { "id3v2_tag", "ID3v2_TAG" }, { "input1", "e_mpegVersion" }, { "input2", "e_layerVersion" }, { "input3", "e_protectionBit" }, { "input4", "e_bitRateIndexV1L1" }, { "input5", "e_samplingRateIndexV1" }, { "input6", "e_paddingBit" }, { "input7", "e_privateBit" }, { "input8", "e_channelMode" }, { "input9", "e_modeExtensionL1L2" }, { "input10", "e_copyrightBit" }, { "input11", "e_originalBit" }, { "input12", "e_emphasis" }, { "full_hdr", "uint32_class" }, { "crc16", "uint16_class" }, { "mpeg_hdr", "MPEG_HEADER" }, { "mpeg_frame_data", "ubyte_array_class" }, { "mf", "MPEG_FRAME" }, { "title", "char_array_class" }, { "artist", "char_array_class" }, { "album", "char_array_class" }, { "year", "char_array_class" }, { "comment", "char_array_class" }, { "zero", "byte_class" }, { "track", "ubyte_class" }, { "genre", "ID3_GENRES" }, { "id3v1_tag", "ID3v1_TAG" } };

std::vector<std::vector<int>> integer_ranges = { { 1, 16 }, { 3, 4 }, { 2, 4 } };

class globals_class {
public:
	int _struct_id = 0;
	int _struct_id_counter = 0;
	/*local*/ uint32 bitrate;
	/*local*/ uint32 frame_size;
	/*local*/ uint32 sampling_freq;
	/*local*/ uint32 frames_count;
	/*local*/ quad frame_header_offset;
	/*local*/ quad seek_pos;
	/*local*/ quad sum_bitrate;
	/*local*/ uint16 data;
	/*local*/ byte was_bad_sync;
	/*local*/ byte id3v1_tag_found;
	/*local*/ std::string buf;
	/*local*/ uint32 id3v2_size;
	/*local*/ uint32 synchsafe_pos;
	/*local*/ uint32 mpeg_frame_start_pos;
	/*local*/ uint32 id3v2_tag_no_header_start;
	/*local*/ uint32 id3v2_tag_end;
	/*local*/ std::string buf_input;
	/*local*/ std::vector<std::string> buf_values;
	char_class head_element;
	char_array_class head;
	char_class ver_major;
	char_class ver_revision;
	ubyte_class i_unsyn_used;
	ubyte_class i_extend_head_pres;
	ubyte_class i_experiment_tag;
	ubyte_class reserv_flags;
	ubyte_class flags;
	FLAGS flags_;
	ubyte_class first;
	ubyte_class second;
	ubyte_class third;
	ubyte_class fourth;
	ID3v2_HEADER hdr;
	ubyte_class id3v2_data_element;
	ubyte_array_class id3v2_data;
	uint32_class size;
	uint16_bitfield FLAG_CRC_PRESENT;
	uint16_bitfield uint16_bitfield_padding;
	uint32_class padding_sz;
	uint32_class crc;
	ID3v2_EXTENDED_HEADER ext_hdr;
	char_class id_element;
	char_array_class id;
	uint16_bitfield TAG_ALTER_PRESERV;
	uint16_bitfield FILE_ALTER_PRESERV;
	uint16_bitfield READ_ONLY_FRAME;
	uint16_bitfield COMPRESSED_FRAME;
	uint16_bitfield ENCRYPTED_FRAME;
	uint16_bitfield GROUP_MEMBER_FRAME;
	FRAME_FLAGS flags__;
	byte_class id_asciiz_str;
	char_class frame_data_element;
	char_array_class frame_data;
	ubyte_class frame_data__element;
	ubyte_array_class frame_data_;
	ID3v2_FRAME tf;
	ID3v2_4_FRAME tf_;
	ubyte_class id3v2_padding_element;
	ubyte_array_class id3v2_padding;
	ID3v2_TAG id3v2_tag;
	/*local*/ std::vector<ushort> data_values;
	uint32_class full_hdr;
	uint16_class crc16;
	MPEG_HEADER mpeg_hdr;
	ubyte_class mpeg_frame_data_element;
	ubyte_array_class mpeg_frame_data;
	MPEG_FRAME mf;
	char_class title_element;
	char_array_class title;
	char_class artist_element;
	char_array_class artist;
	char_class album_element;
	char_array_class album;
	char_class year_element;
	char_array_class year;
	char_class comment_element;
	char_array_class comment;
	byte_class zero;
	ubyte_class track;
	ID3v1_TAG id3v1_tag;


	globals_class() :
		head_element(false),
		head(head_element),
		ver_major(3),
		ver_revision(4),
		i_unsyn_used(1),
		i_extend_head_pres(1),
		i_experiment_tag(1),
		reserv_flags(1),
		flags(1),
		flags_(FLAGS_flags__instances),
		first(1),
		second(1),
		third(1),
		fourth(1),
		hdr(ID3v2_HEADER_hdr_instances),
		id3v2_data_element(false),
		id3v2_data(id3v2_data_element),
		size(1),
		FLAG_CRC_PRESENT(1),
		uint16_bitfield_padding(1),
		padding_sz(1),
		crc(1),
		ext_hdr(ID3v2_EXTENDED_HEADER_ext_hdr_instances),
		id_element(false),
		id(id_element, { { 0, {{'T', 'T'}} } }),
		TAG_ALTER_PRESERV(1),
		FILE_ALTER_PRESERV(1),
		READ_ONLY_FRAME(1),
		COMPRESSED_FRAME(1),
		ENCRYPTED_FRAME(1),
		GROUP_MEMBER_FRAME(1),
		flags__(FRAME_FLAGS_flags___instances),
		id_asciiz_str(1),
		frame_data_element(false),
		frame_data(frame_data_element),
		frame_data__element(false),
		frame_data_(frame_data__element),
		tf(ID3v2_FRAME_tf_instances),
		tf_(ID3v2_4_FRAME_tf__instances),
		id3v2_padding_element(false),
		id3v2_padding(id3v2_padding_element),
		id3v2_tag(ID3v2_TAG_id3v2_tag_instances),
		full_hdr(1),
		crc16(1),
		mpeg_hdr(MPEG_HEADER_mpeg_hdr_instances),
		mpeg_frame_data_element(false),
		mpeg_frame_data(mpeg_frame_data_element),
		mf(MPEG_FRAME_mf_instances),
		title_element(false),
		title(title_element),
		artist_element(false),
		artist(artist_element),
		album_element(false),
		album(album_element),
		year_element(false),
		year(year_element),
		comment_element(false),
		comment(comment_element),
		zero(1),
		track(1),
		id3v1_tag(ID3v1_TAG_id3v1_tag_instances)
	{}
};

globals_class* g;

void write_synchsafe_integer(uint32 size) {
	/*local*/ ubyte f_first = 0;
	/*local*/ ubyte f_second = 0;
	/*local*/ ubyte f_third = 0;
	/*local*/ ubyte f_fourth = 0;
	if ((size > 0xFFFFFFF)) {
		Printf("Size: %zu is too large!\n", size);
	};
	/*local*/ uint32 i = 0;
	/*local*/ std::vector<ubyte> size_bit_array(32);
	for (i = 0; (i <= 31); i++) {
			if (((((i == 7) || (i == 15)) || (i == 23)) || (i == 31))) {
			size_bit_array[i] = 0;
		} else {
			size_bit_array[i] = ((size >> i) % 2);
		};
	;
	};
	for (i = 0; (i <= 32); i++) {
			switch ((i / 8)) {
		case 0:
			f_first += (size_bit_array[i] << (i % 8));
			break;
		case 1:
			f_second += (size_bit_array[i] << (i % 8));
			break;
		case 2:
			f_third += (size_bit_array[i] << (i % 8));
			break;
		default:
			f_fourth += (size_bit_array[i] << (i % 8));
			break;
		};
	;
	};
	GENERATE(first, ::g->first.generate({ f_first }));
	GENERATE(second, ::g->second.generate({ f_second }));
	GENERATE(third, ::g->third.generate({ f_third }));
	GENERATE(fourth, ::g->fourth.generate({ f_fourth }));
	Printf("First: %d\nSecond: %d\nThird: %d\nFourth: %d\n", f_first, f_second, f_third, f_fourth);
	if (((((f_first >= 0x80) || (f_second >= 0x80)) || (f_third >= 0x80)) || (f_fourth >= 0x80))) {
		Printf("MP3: warning: invalid ID3v2 synchsafe integer\n");
	};
}

FLAGS* FLAGS::generate() {
	if (generated == 1) {
		FLAGS* new_instance = new FLAGS(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	current_pos = FTell();
	full_flags = 0;
	GENERATE_VAR(i_unsyn_used, ::g->i_unsyn_used.generate({ 0 }));
	unsyn_used = (i_unsyn_used() << 7);
	FSeek(current_pos);
	GENERATE_VAR(i_extend_head_pres, ::g->i_extend_head_pres.generate({ 0 }));
	extend_head_pres = (i_extend_head_pres() << 6);
	FSeek(current_pos);
	GENERATE_VAR(i_experiment_tag, ::g->i_experiment_tag.generate({ 0 }));
	experiment_tag = (i_experiment_tag() << 5);
	FSeek(current_pos);
	GENERATE_VAR(reserv_flags, ::g->reserv_flags.generate({ 0 }));
	FSeek(current_pos);
	full_flags += (((unsyn_used + extend_head_pres) + experiment_tag) + reserv_flags());
	GENERATE_VAR(flags, ::g->flags.generate({ full_flags }));
	UNSYNCHRONISATION_USED = (unsyn_used >> 7);
	EXTENDED_HEADER_PRESENT = (extend_head_pres >> 6);
	EXPERIMENTAL_TAG = (experiment_tag >> 5);
	RESERVED_FLAGS = reserv_flags();

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


ID3v2_HEADER* ID3v2_HEADER::generate() {
	if (generated == 1) {
		ID3v2_HEADER* new_instance = new ID3v2_HEADER(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	GENERATE_VAR(head, ::g->head.generate(3, { "ID3" }));
	GENERATE_VAR(ver_major, ::g->ver_major.generate());
	GENERATE_VAR(ver_revision, ::g->ver_revision.generate());
	GENERATE_VAR(flags, ::g->flags_.generate());
	DisplayFormatHex();
	::g->synchsafe_pos = FTell();
	FSeek((FTell() - 4));
	write_synchsafe_integer(size);

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


ID3v2_EXTENDED_HEADER* ID3v2_EXTENDED_HEADER::generate() {
	if (generated == 1) {
		ID3v2_EXTENDED_HEADER* new_instance = new ID3v2_EXTENDED_HEADER(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	SetBackColor(0xA1D4FF);
	DisplayFormatDecimal();
	GENERATE_VAR(size, ::g->size.generate());
	GENERATE_VAR(FLAG_CRC_PRESENT, ::g->FLAG_CRC_PRESENT.generate(1));
	GENERATE_VAR(uint16_bitfield_padding, ::g->uint16_bitfield_padding.generate(15));
	GENERATE_VAR(padding_sz, ::g->padding_sz.generate());
	if (FLAG_CRC_PRESENT()) {
		DisplayFormatHex();
		GENERATE_VAR(crc, ::g->crc.generate());
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


FRAME_FLAGS* FRAME_FLAGS::generate() {
	if (generated == 1) {
		FRAME_FLAGS* new_instance = new FRAME_FLAGS(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	GENERATE_VAR(TAG_ALTER_PRESERV, ::g->TAG_ALTER_PRESERV.generate(1));
	GENERATE_VAR(FILE_ALTER_PRESERV, ::g->FILE_ALTER_PRESERV.generate(1));
	GENERATE_VAR(READ_ONLY_FRAME, ::g->READ_ONLY_FRAME.generate(1));
	GENERATE_VAR(uint16_bitfield_padding, ::g->uint16_bitfield_padding.generate(5));
	GENERATE_VAR(COMPRESSED_FRAME, ::g->COMPRESSED_FRAME.generate(1));
	GENERATE_VAR(ENCRYPTED_FRAME, ::g->ENCRYPTED_FRAME.generate(1));
	GENERATE_VAR(GROUP_MEMBER_FRAME, ::g->GROUP_MEMBER_FRAME.generate(1));
	GENERATE_VAR(uint16_bitfield_padding, ::g->uint16_bitfield_padding.generate(5));

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


ID3v2_FRAME* ID3v2_FRAME::generate() {
	if (generated == 1) {
		ID3v2_FRAME* new_instance = new ID3v2_FRAME(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	Printf("ID3v2 frame alpha chars \n");
	GENERATE_VAR(id, ::g->id.generate(4, { "TALB", "TBPM", "TCOM", "TCON", "TCOP", "TDEN", "TDLY", "TDOR", "TDRC", "TDRL", "TDTG", "TENC", "TEXT", "TFLT", "TIPL", "TIT1", "TIT2", "TIT3", "TKEY", "TLAN", "TLEN", "TMCL", "TMED", "TMOO", "TOAL", "TOFN", "TOLY", "TOPE", "TOWN", "TPE1", "TPE2", "TPE3", "TPE4", "TPOS", "TPRO", "TPUB", "TRCK", "TRSN", "TRSO", "TSOA", "TSOP", "TSOT", "TSRC", "TSSE", "TSST" }));
	DisplayFormatDecimal();
	id3v2_frame_size_location = FTell();
	GENERATE_VAR(size, ::g->size.generate());
	GENERATE_VAR(flags, ::g->flags__.generate());
	if ((id()[0] == 'T')) {
		if (((ReadByte(FTell()) == 0) && (size() > 1))) {
			GENERATE_VAR(id_asciiz_str, ::g->id_asciiz_str.generate());
			Printf("ID3v2 frame frame_data \n");
			GENERATE(frame_data, ::g->frame_data.generate((size() - 1)));
		} else {
		Printf("Size: %d\n", size());
		};
		Printf("ID3v2 frame frame_data else \n");
		GENERATE(frame_data, ::g->frame_data.generate(size()));
	} else {
		DisplayFormatHex();
		Printf("ID3v2 frame frame_data else 2 \n");
		GENERATE(frame_data, ::g->frame_data_.generate(size()));
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


ID3v2_4_FRAME* ID3v2_4_FRAME::generate() {
	if (generated == 1) {
		ID3v2_4_FRAME* new_instance = new ID3v2_4_FRAME(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	Printf("ID3v2.4 frame alpha chars \n");
	GENERATE_VAR(id, ::g->id.generate(4, { "TALB", "TBPM", "TCOM", "TCON", "TCOP", "TDEN", "TDLY", "TDOR", "TDRC", "TDRL", "TDTG", "TENC", "TEXT", "TFLT", "TIPL", "TIT1", "TIT2", "TIT3", "TKEY", "TLAN", "TLEN", "TMCL", "TMED", "TMOO", "TOAL", "TOFN", "TOLY", "TOPE", "TOWN", "TPE1", "TPE2", "TPE3", "TPE4", "TPOS", "TPRO", "TPUB", "TRCK", "TRSN", "TRSO", "TSOA", "TSOP", "TSOT", "TSRC", "TSSE", "TSST" }));
	DisplayFormatDecimal();
	id3v2_4_synchsafe_pos = FTell();
	GENERATE_VAR(size, ::g->size.generate());
	FSeek((FTell() - 4));
	write_synchsafe_integer(size());
	id3v2_4_frame_start_no_header = FTell();
	GENERATE_VAR(flags, ::g->flags__.generate());
	if ((id()[0] == 'T')) {
		GENERATE_VAR(encoding, encoding_enum_generate());
		Printf("Size: %d\n", (size() - 1));
		Printf("ID3v2.4 frame frame_data \n");
		GENERATE(frame_data, ::g->frame_data.generate((size() - 1)));
	} else {
		DisplayFormatHex();
		Printf("Size: %d\n", size());
		Printf("ID3v2.4 frame frame_data else \n");
		GENERATE(frame_data, ::g->frame_data_.generate(size()));
	};
	id3v2_4_frame_end = FTell();
	FSeek(id3v2_4_synchsafe_pos);
	id3v2_4_frame_size = (id3v2_4_frame_end - id3v2_4_frame_start_no_header);
	write_synchsafe_integer(id3v2_4_frame_size);
	FSeek(id3v2_4_frame_end);

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


ID3v2_TAG* ID3v2_TAG::generate() {
	if (generated == 1) {
		ID3v2_TAG* new_instance = new ID3v2_TAG(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	GENERATE_VAR(hdr, ::g->hdr.generate());
	::g->id3v2_tag_no_header_start = FTell();
	tag_sz = hdr().size;
	Printf("tag_sz: %d, hdr.size.computed: %d\n", tag_sz, hdr().size);
	if (((hdr().ver_major() == 0xFF) || (hdr().ver_revision() == 0xFF))) {
		Printf("MP3: warning: invalid ID3v2 tag header\n");
	} else {
		if (((!((hdr().ver_major() == 3) || (hdr().ver_major() == 4)) || hdr().flags().UNSYNCHRONISATION_USED) || hdr().flags().EXPERIMENTAL_TAG)) {
			Printf("Major: %d, Version: %d, Unsync: %d, Exp: %d\n", hdr().ver_major(), hdr().ver_revision(), hdr().flags().UNSYNCHRONISATION_USED, hdr().flags().EXPERIMENTAL_TAG);
			Printf("MP3: warning: skipping unsupported ID3v2.%d tag\n", hdr().ver_major());
			SetBackColor(0xA9DCFF);
			DisplayFormatHex();
			Printf("Unsupported ID3v2_data \n");
			GENERATE_VAR(id3v2_data, ::g->id3v2_data.generate(tag_sz));
		} else {
			if (hdr().flags().EXTENDED_HEADER_PRESENT) {
				GENERATE_VAR(ext_hdr, ::g->ext_hdr.generate());
			};
			frame_color = 0xC9FCFF;
			do {
				SetBackColor(frame_color);
				if ((hdr().ver_major() == 3)) {
					GENERATE(tf, ::g->tf.generate());
				} else {
					GENERATE(tf, ::g->tf_.generate());
				};
				frame_color -= 0x020200;
			} while (((FTell() < (tag_sz + hdr()._sizeof)) && (ReadByte(FTell()) != 0)));
			SetBackColor(0x99CCFF);
			Printf("tag_sz: %d\nsizeof(hdr): %d\nFtell(): %d\n", tag_sz, hdr()._sizeof, FTell());
			Printf("Size: %d\n", ((tag_sz + hdr()._sizeof) - FTell()));
			Printf("id3v2_padding \n");
			GENERATE_VAR(id3v2_padding, ::g->id3v2_padding.generate(((tag_sz + hdr()._sizeof) - FTell())));
		};
	};
	::g->id3v2_tag_end = FTell();
	id3v2_tag_full_size = (::g->id3v2_tag_end - ::g->id3v2_tag_no_header_start);
	FSeek(::g->synchsafe_pos);
	size = id3v2_tag_full_size;
	FSeek((FTell() - 4));
	write_synchsafe_integer(size);
	FSeek(::g->id3v2_tag_end);

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


MPEG_HEADER* MPEG_HEADER::generate() {
	if (generated == 1) {
		MPEG_HEADER* new_instance = new MPEG_HEADER(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	DisplayFormatHex();
	mpeg_header_start = FTell();
	current_pos = FTell();
	full_input = 0;
	frame_sync = 0xFFF;
	frame_sync = (frame_sync << 20);
	full_input += frame_sync;
	GENERATE_VAR(input1, e_mpegVersion_generate());
	mpeg_id = input1();
	mpeg_id = (mpeg_id << 19);
	full_input += mpeg_id;
	FSeek(current_pos);
	GENERATE_VAR(input2, e_layerVersion_generate());
	layer_id = input2();
	layer_id = (layer_id << 17);
	full_input += layer_id;
	FSeek(current_pos);
	GENERATE_VAR(input3, e_protectionBit_generate());
	protection_bit = input3();
	protection_bit = (protection_bit << 16);
	full_input += protection_bit;
	FSeek(current_pos);
	bitrate_index = 0;
	switch (mpeg_id) {
	case 0:
		switch (layer_id) {
		case 1:
			GENERATE_VAR(input4, e_bitRateIndexV2L2L3_generate());
			bitrate_index = input4();
			FSeek(current_pos);
			break;
		case 2:
			GENERATE_VAR(input4, e_bitRateIndexV2L2L3_generate());
			bitrate_index = input4();
			FSeek(current_pos);
			break;
		default:
			GENERATE_VAR(input4, e_bitRateIndexV2L1_generate());
			bitrate_index = input4();
			FSeek(current_pos);
			break;
		};
		break;
	case 2:
		switch (layer_id) {
		case 1:
			GENERATE_VAR(input4, e_bitRateIndexV2L2L3_generate());
			bitrate_index = input4();
			FSeek(current_pos);
			break;
		case 2:
			GENERATE_VAR(input4, e_bitRateIndexV2L2L3_generate());
			bitrate_index = input4();
			FSeek(current_pos);
			break;
		default:
			GENERATE_VAR(input4, e_bitRateIndexV2L1_generate());
			bitrate_index = input4();
			FSeek(current_pos);
			break;
		};
		break;
	default:
		switch (layer_id) {
		case 1:
			GENERATE_VAR(input4, e_bitRateIndexV1L3_generate());
			bitrate_index = input4();
			FSeek(current_pos);
			break;
		case 2:
			GENERATE_VAR(input4, e_bitRateIndexV1L2_generate());
			bitrate_index = input4();
			FSeek(current_pos);
			break;
		default:
			GENERATE_VAR(input4, e_bitRateIndexV1L1_generate());
			bitrate_index = input4();
			FSeek(current_pos);
		};
		break;
	};
	bitrate_index = (bitrate_index << 12);
	full_input += bitrate_index;
	frequency_index = 0;
	switch (mpeg_id) {
	case 0:
		GENERATE_VAR(input5, e_samplingRateIndexV25_generate());
		frequency_index = input5();
		FSeek(current_pos);
		break;
	case 2:
		GENERATE_VAR(input5, e_samplingRateIndexV2_generate());
		frequency_index = input5();
		FSeek(current_pos);
		break;
	default:
		GENERATE_VAR(input5, e_samplingRateIndexV1_generate());
		frequency_index = input5();
		FSeek(current_pos);
		break;
	};
	frequency_index = (frequency_index << 10);
	full_input += frequency_index;
	GENERATE_VAR(input6, e_paddingBit_generate());
	padding_bit = input6();
	padding_bit = (padding_bit << 9);
	full_input += padding_bit;
	FSeek(current_pos);
	GENERATE_VAR(input7, e_privateBit_generate());
	private_bit = input7();
	private_bit = (private_bit << 8);
	full_input += private_bit;
	FSeek(current_pos);
	channel_mode = 0;
	switch (layer_id) {
	case 1:
		GENERATE_VAR(input8, e_channelMode_generate());
		channel_mode = input8();
		FSeek(current_pos);
		break;
	case 2:
		switch (bitrate_index) {
		case 0:
			GENERATE_VAR(input8, e_channelMode_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 1:
			GENERATE_VAR(input8, e_channelModeSingle_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 2:
			GENERATE_VAR(input8, e_channelModeSingle_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 3:
			GENERATE_VAR(input8, e_channelModeSingle_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 4:
			GENERATE_VAR(input8, e_channelMode_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 5:
			GENERATE_VAR(input8, e_channelModeSingle_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 6:
			GENERATE_VAR(input8, e_channelMode_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 7:
			GENERATE_VAR(input8, e_channelMode_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 8:
			GENERATE_VAR(input8, e_channelMode_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 9:
			GENERATE_VAR(input8, e_channelMode_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 10:
			GENERATE_VAR(input8, e_channelMode_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 11:
			GENERATE_VAR(input8, e_channelModeNonSingle_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 12:
			GENERATE_VAR(input8, e_channelModeNonSingle_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		case 13:
			GENERATE_VAR(input8, e_channelModeNonSingle_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		default:
			GENERATE_VAR(input8, e_channelModeNonSingle_generate());
			channel_mode = input8();
			FSeek(current_pos);
			break;
		};
		break;
	default:
		GENERATE_VAR(input8, e_channelMode_generate());
		channel_mode = input8();
		FSeek(current_pos);
		break;
	};
	channel_mode = (channel_mode << 6);
	full_input += channel_mode;
	GENERATE_VAR(input9, e_modeExtensionL1L2_generate());
	mode_extension = input9();
	mode_extension = (mode_extension << 4);
	full_input += mode_extension;
	FSeek(current_pos);
	GENERATE_VAR(input10, e_copyrightBit_generate());
	copyright = input10();
	copyright = (copyright << 3);
	full_input += copyright;
	FSeek(current_pos);
	GENERATE_VAR(input11, e_originalBit_generate());
	original = input11();
	original = (original << 2);
	full_input += original;
	FSeek(current_pos);
	GENERATE_VAR(input12, e_emphasis_generate());
	emphasis = input12();
	full_input += emphasis;
	FSeek(current_pos);
	GENERATE_VAR(full_hdr, ::g->full_hdr.generate({ full_input }));
	mpeg_header_end = FTell();
	mpeg_header_size = (mpeg_header_end - mpeg_header_start);
	if ((input3() == 0)) {
		crc_calc = Checksum(CHECKSUM_CRC16, mpeg_header_start, mpeg_header_size);
		GENERATE_VAR(crc16, ::g->crc16.generate({ crc_calc }));
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


MPEG_FRAME* MPEG_FRAME::generate() {
	if (generated == 1) {
		MPEG_FRAME* new_instance = new MPEG_FRAME(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	GENERATE_VAR(mpeg_hdr, ::g->mpeg_hdr.generate());
	::g->bitrate = 0;
	if ((((((mpeg_hdr().frame_sync < 0xFFE) || (mpeg_hdr().layer_id == 0)) || (mpeg_hdr().bitrate_index == 0)) || (mpeg_hdr().bitrate_index == 15)) || (mpeg_hdr().frequency_index == 3))) {
		Printf("MP3: warning: invalid MPEG header in frame at offset 0x%X\n", ((FTell() - 4) - ((mpeg_hdr().protection_bit == 0) ? 2 : 0)));
		FSeek((FTell() - 2));
	} else {
		if ((mpeg_hdr().layer_id == 3)) {
			::g->bitrate = ((uint32)mpeg_hdr().bitrate_index << 5);
		} else {
			if ((mpeg_hdr().layer_id == 2)) {
				::g->bitrate = (((uint32)mpeg_hdr().bitrate_index == 1) ? 32 : ((1 << (5 + ((uint32)mpeg_hdr().bitrate_index / 4))) + (((uint32)mpeg_hdr().bitrate_index & 3) << (3 + ((uint32)mpeg_hdr().bitrate_index / 4)))));
			} else {
				if ((mpeg_hdr().mpeg_id == 1)) {
					::g->bitrate = ((1 << (5 + (((uint32)mpeg_hdr().bitrate_index - 1) / 4))) + ((((uint32)mpeg_hdr().bitrate_index - 1) & 3) << (3 + (((uint32)mpeg_hdr().bitrate_index - 1) / 4))));
				} else {
					::g->bitrate = (((uint32)mpeg_hdr().bitrate_index < 4) ? (8 * (uint32)mpeg_hdr().bitrate_index) : ((1 << (4 + ((uint32)mpeg_hdr().bitrate_index / 4))) + ((((uint32)mpeg_hdr().bitrate_index & 3) == 0) ? 0 : ((((uint32)mpeg_hdr().bitrate_index & 3) == 1) ? (1 << (4 + ((uint32)mpeg_hdr().bitrate_index / 4))) : ((((uint32)mpeg_hdr().bitrate_index & 3) == 2) ? ((1 << (4 + ((uint32)mpeg_hdr().bitrate_index / 4))) + ((1 << (4 + ((uint32)mpeg_hdr().bitrate_index / 4))) >> 1)) : ((1 << (4 + ((uint32)mpeg_hdr().bitrate_index / 4))) - ((1 << (4 + ((uint32)mpeg_hdr().bitrate_index / 4))) >> 2)))))));
				};
			};
		};
	};
	if ((::g->bitrate != 0)) {
		fr0 = 2205;
		fr1 = 2400;
		fr2 = 1600;
		::g->sampling_freq = 1600;
		if ((mpeg_hdr().frequency_index == 0)) {
			::g->sampling_freq = fr0;
		};
		if ((mpeg_hdr().frequency_index == 1)) {
			::g->sampling_freq = fr1;
		};
		if ((mpeg_hdr().frequency_index == 2)) {
			::g->sampling_freq = fr2;
		};
		if ((mpeg_hdr().mpeg_id == 1)) {
		::g->sampling_freq <<= 1;
		};
		::g->frame_size = ((::g->bitrate * 14400) / ::g->sampling_freq);
		if ((mpeg_hdr().channel_mode == 3)) {
		::g->frame_size >>= 1;
		};
		::g->frame_size -= ((4 + ((mpeg_hdr().protection_bit == 0) ? 2 : 0)) - mpeg_hdr().padding_bit);
		::g->frame_header_offset = ((FTell() - 4) - ((mpeg_hdr().protection_bit == 0) ? 2 : 0));
		if (((FTell() + ::g->frame_size) > FileSize())) {
			Printf("MP3: warning: cut MPEG frame at end of file (frame header offset = 0x%LX, data length = %u)\n", ::g->frame_header_offset, ::g->frame_size);
			Printf("MP3: file parsing completed!\nMP3: valid MPEG frames found: %d\n", ::g->frames_count);
			if ((::g->frames_count != 0)) {
			Printf("MP3: average frame bitrate: %d kbit\n", (::g->sum_bitrate / ::g->frames_count));
			};
			exit_template(-1);
		} else {
			DisplayFormatHex();
			SetBackColor(0xCCCCFF);
			Printf("mpeg_frame_data \n");
			GENERATE_VAR(mpeg_frame_data, ::g->mpeg_frame_data.generate(::g->frame_size));
		};
		::g->sum_bitrate += ::g->bitrate;
		::g->frames_count++;
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


ID3v1_TAG* ID3v1_TAG::generate() {
	if (generated == 1) {
		ID3v1_TAG* new_instance = new ID3v1_TAG(instances);
		new_instance->generated = 2;
		return new_instance->generate();
	}
	if (!generated)
		generated = 1;
	_startof = FTell();
	if (_parent_id != ::g->_struct_id && !global_indexing_of_arrays) {
		_index_start = instances.size() - 1;
	}
	_parent_id = ::g->_struct_id;
	::g->_struct_id = ++::g->_struct_id_counter;

	DisplayFormatDecimal();
	SetBackColor(0x33BC55);
	Printf("ID3v1 charID \n");
	GENERATE_VAR(id, ::g->id.generate(3, { "TAG" }));
	SetBackColor(0x48E048);
	Printf("ID3v1 title \n");
	GENERATE_VAR(title, ::g->title.generate(30));
	SetBackColor(0x5DE45D);
	Printf("ID3v1 artist \n");
	GENERATE_VAR(artist, ::g->artist.generate(30));
	SetBackColor(0x72E872);
	Printf("ID3v1 album \n");
	GENERATE_VAR(album, ::g->album.generate(30));
	SetBackColor(0x87EC87);
	Printf("ID3v1 year \n");
	GENERATE_VAR(year, ::g->year.generate(4));
	if (((ReadByte((FTell() + 28)) == 0) && (ReadByte((FTell() + 29)) != 0))) {
		SetBackColor(0x9CF09C);
		Printf("ID3v1.1 comment \n");
		GENERATE_VAR(comment, ::g->comment.generate(28));
		SetBackColor(0xB1F4B1);
		GENERATE_VAR(zero, ::g->zero.generate({ 0 }));
		SetBackColor(0xC6F8C6);
		GENERATE_VAR(track, ::g->track.generate());
	} else {
		SetBackColor(0x9CF09C);
		Printf("ID3v1.0 comment \n");
		GENERATE_VAR(comment, ::g->comment.generate(30));
	};
	SetBackColor(0xDBFCDB);
	GENERATE_VAR(genre, ID3_GENRES_generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}



void generate_file() {
	::g = new globals_class();

	::g->frames_count = 0;
	::g->sum_bitrate = 0;
	::g->id3v1_tag_found = 0;
	::g->buf.resize(3);
	::g->id3v2_size = 0;
	::g->synchsafe_pos = 0;
	::g->mpeg_frame_start_pos = 0;
	::g->id3v2_tag_no_header_start = 0;
	::g->id3v2_tag_end = 0;
	BigEndian();
	BigEndian();
	::g->buf_input.resize(3);
	::g->buf_values = { "ID3" };
	ReadBytes(::g->buf, 0, 3, ::g->buf_values);
	if (!Strcmp(::g->buf, "ID3")) {
		Printf("MP3: ID3v2 tag found\n");
		GENERATE(id3v2_tag, ::g->id3v2_tag.generate());
	};
	::g->data_values = { 0x5441 };
	while ((!FEof() && !::g->id3v1_tag_found)) {
		::g->seek_pos = FTell();
		::g->was_bad_sync = 0;
		do {
			::g->data = ReadUShort(::g->seek_pos, ::g->data_values);
			if (((::g->data == 0x5441) && (ReadUByte((::g->seek_pos + 2)) == 0x47))) {
			::g->id3v1_tag_found = 1;
			};
			if (((!::g->was_bad_sync && (::g->data < 0xFFE0)) && !::g->id3v1_tag_found)) {
				Printf("MP3: warning: invalid MPEG frame synchronization at offset 0x%LX\n", ::g->seek_pos);
				::g->was_bad_sync = 1;
			};
			::g->seek_pos++;
		} while ((((::g->data < 0xFFE0) && (::g->seek_pos < (FileSize() - 1))) && !::g->id3v1_tag_found));
		if (((::g->data >= 0xFFE0) || ::g->id3v1_tag_found)) {
			FSeek((::g->seek_pos - 1));
		} else {
			Printf("MP3: file parsing completed!\nMP3: valid MPEG frames found: %d\n", ::g->frames_count);
			if ((::g->frames_count != 0)) {
			Printf("MP3: average frame bitrate: %d kbit\n", (::g->sum_bitrate / ::g->frames_count));
			};
			exit_template(0);
		};
		if (!::g->id3v1_tag_found) {
			GENERATE(mf, ::g->mf.generate());
			if (((::g->frames_count == 1) && ::g->bitrate)) {
			Printf("MP3: first found MPEG frame parameters:\nMP3:\t- header ofsset: 0x%LX\nMP3:\t- bitrate: %d kbit\nMP3:\t- MPEG-%d layer %d\nMP3:\t- sampling frequency: %d Hz\nMP3:\t- channel mode: %s\nMP3:\t- CRC protected: %s\n", ::g->frame_header_offset, ::g->bitrate, ((::g->mf().mpeg_hdr().mpeg_id == 1) ? 1 : 2), ((::g->mf().mpeg_hdr().layer_id == 1) ? 3 : ((::g->mf().mpeg_hdr().layer_id == 2) ? 2 : 1)), (::g->sampling_freq * 10), std::string(((::g->mf().mpeg_hdr().channel_mode == 3) ? "mono" : ((::g->mf().mpeg_hdr().channel_mode == 0) ? "stereo" : ((::g->mf().mpeg_hdr().channel_mode == 1) ? "joint stereo" : "dual channel")))).c_str(), std::string(((::g->mf().mpeg_hdr().protection_bit == 0) ? "Yes" : "No")).c_str());
			};
		};
	};
	if (::g->id3v1_tag_found) {
		Printf("MP3: ID3v1 tag found\n");
		GENERATE(id3v1_tag, ::g->id3v1_tag.generate());
	};
	if (!FEof()) {
	Printf("MP3: warning: there is some unknown extra-data after ID3v1 tag at end of file\n");
	};
	Printf("MP3: file parsing completed!\nMP3: valid MPEG frames found: %d\n", ::g->frames_count);
	if ((::g->frames_count != 0)) {
	Printf("MP3: average frame bitrate: %d kbit\n", (::g->sum_bitrate / ::g->frames_count));
	};

	file_acc.finish();
	delete_globals();
}

void delete_globals() { delete ::g; }

