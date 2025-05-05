#include <cstdlib>
#include <cstdio>
#include <string>
#include <vector>
#include <unordered_map>
#include "bt.h"

enum qtlang {
	qtlEnglish = 0,
	qtlFrench = 1,
	qtlGerman = 2,
	qtlItalian = 3,
	qtlDutch = 4,
	qtlSwedish = 5,
	qtlSpanish = 6,
	qtlDanish = 7,
	qtlPortuguese = 8,
	qtlNorwegian = 9,
	qtlHebrew = 10,
	qtlJapanese = 11,
	qtlArabic = 12,
	qtlFinnish = 13,
	qtlGreek = 14,
	qtlIcelandic = 15,
	qtlMaltese = 16,
	qtlTurkish = 17,
	qtlCroatian = 18,
	qtlChineseTraditional = 19,
	qtlUrdu = 20,
	qtlHindi = 21,
	qtlThai = 22,
	qtlKorean = 23,
	qtlLithuanian = 24,
	qtlPolish = 25,
	qtlHungarian = 26,
	qtlEstonian = 27,
	qtlLettish = 28,
	qtlLatvian = 28,
	qtlSaami = 29,
	qtlSami = 29,
	qtlFaroese = 30,
	qtlFarsi = 31,
	qtlRussian = 32,
	qtlChineseSimplified = 33,
	qtlFlemish = 34,
	qtlIrish = 35,
	qtlAlbanian = 36,
	qtlRomanian = 37,
	qtlCzech = 38,
	qtlSlovak = 39,
	qtlSlovenian = 40,
	qtlYiddish = 41,
	qtlSerbian = 42,
	qtlMacedonian = 43,
	qtlBulgarian = 44,
	qtlUkrainian = 45,
	qtlBelarusian = 46,
	qtlUzbek = 47,
	qtlKazakh = 48,
	qtlAzerbaijani = 49,
	qtlAzerbaijanAr = 50,
	qtlArmenian = 51,
	qtlGeorgian = 52,
	qtlMoldavian = 53,
	qtlKirghiz = 54,
	qtlTajiki = 55,
	qtlTurkmen = 56,
	qtlMongolian = 57,
	qtlMongolianCyr = 58,
	qtlPashto = 59,
	qtlKurdish = 60,
	qtlKashmiri = 61,
	qtlSindhi = 62,
	qtlTibetan = 63,
	qtlNepali = 64,
	qtlSanskrit = 65,
	qtlMarathi = 66,
	qtlBengali = 67,
	qtlAssamese = 68,
	qtlGujarati = 69,
	qtlPunjabi = 70,
	qtlOriya = 71,
	qtlMalayalam = 72,
	qtlKannada = 73,
	qtlTamil = 74,
	qtlTelugu = 75,
	qtlSinhala = 76,
	qtlBurmese = 77,
	qtlKhmer = 78,
	qtlLao = 79,
	qtlVietnamese = 80,
	qtlIndonesian = 81,
	qtlTagalog = 82,
	qtlMalayRoman = 83,
	qtlMalayArabic = 84,
	qtlAmharic = 85,
	qtlGalla = 87,
	qtlOromo = 87,
	qtlSomali = 88,
	qtlSwahili = 89,
	qtlKinyarwanda = 90,
	qtlRundi = 91,
	qtlNyanja = 92,
	qtlMalagasy = 93,
	qtlEsperanto = 94,
	qtlWelsh = 128,
	qtlBasque = 129,
	qtlCatalan = 130,
	qtlLatin = 131,
	qtlQuechua = 132,
	qtlGuarani = 133,
	qtlAymara = 134,
	qtlTatar = 135,
	qtlUighur = 136,
	qtlDzongkha = 137,
	qtlJavaneseRom = 138,
	qtlUnspecified = 32767,
};

enum qtgfxmode : uint16 {
	qtgCopy = (uint16) 0x000,
	qtgDitherCopy = (uint16) 0x040,
	qtgBlend = (uint16) 0x020,
	qtgTransparent = (uint16) 0x024,
	qtgStraightAlpha = (uint16) 0x100,
	qtgPremulWhiteAlpha = (uint16) 0x101,
	qtgPremulBlackAlpha = (uint16) 0x102,
	qtgStraightAlphaBlend = (uint16) 0x104,
	qtgComposition = (uint16) 0x103,
};
std::vector<uint16> qtgfxmode_values = { qtgCopy, qtgDitherCopy, qtgBlend, qtgTransparent, qtgStraightAlpha, qtgPremulWhiteAlpha, qtgPremulBlackAlpha, qtgStraightAlphaBlend, qtgComposition };


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



class fourcc {
	std::vector<fourcc*>& instances;

	std::string value_var;

public:
	bool value_exists = false;

	std::string& value() {
		assert_cond(value_exists, "struct field value does not exist");
		return value_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	fourcc& operator () () { return *instances.back(); }
	fourcc& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	fourcc(std::vector<fourcc*>& instances) : instances(instances) { instances.push_back(this); }
	~fourcc() {
		if (generated == 2)
			return;
		while (instances.size()) {
			fourcc* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	fourcc* generate();
};

int fourcc::_parent_id = 0;
int fourcc::_index_start = 0;


class mp4box;



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



class byte_array_class {
	byte_class& element;
	std::unordered_map<int, std::vector<byte>> element_known_values;
	std::vector<byte> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<byte>& operator () () { return value; }
	byte operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	byte_array_class(byte_class& element, std::unordered_map<int, std::vector<byte>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}

	std::vector<byte> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			auto known = element_known_values.find(i);
			if (known == element_known_values.end()) {
				value.push_back(element.generate());
				_sizeof += element._sizeof;
			} else {
				value.push_back(file_acc.file_integer(sizeof(byte), 0, known->second));
				_sizeof += sizeof(byte);
			}
		}
		return value;
	}
};



class int32_class {
	int small;
	std::vector<int32> known_values;
	int32 value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(int32);
	int32 operator () () { return value; }
	int32_class(int small, std::vector<int32> known_values = {}) : small(small), known_values(known_values) {}

	int32 generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(int32), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(int32), 0, known_values);
		}
		return value;
	}

	int32 generate(std::vector<int32> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(int32), 0, possible_values);
		return value;
	}
};



class fp32 {
	std::vector<fp32*>& instances;

	int32 value_var;

public:
	bool value_exists = false;

	int32& value() {
		assert_cond(value_exists, "struct field value does not exist");
		return value_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	fp32& operator () () { return *instances.back(); }
	fp32& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	fp32(std::vector<fp32*>& instances) : instances(instances) { instances.push_back(this); }
	~fp32() {
		if (generated == 2)
			return;
		while (instances.size()) {
			fp32* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	fp32* generate();
};

int fp32::_parent_id = 0;
int fp32::_index_start = 0;



class int16_class {
	int small;
	std::vector<int16> known_values;
	int16 value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(int16);
	int16 operator () () { return value; }
	int16_class(int small, std::vector<int16> known_values = {}) : small(small), known_values(known_values) {}

	int16 generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(int16), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(int16), 0, known_values);
		}
		return value;
	}

	int16 generate(std::vector<int16> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(int16), 0, possible_values);
		return value;
	}
};



class fp16 {
	std::vector<fp16*>& instances;

	int16 value_var;

public:
	bool value_exists = false;

	int16& value() {
		assert_cond(value_exists, "struct field value does not exist");
		return value_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	fp16& operator () () { return *instances.back(); }
	fp16& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	fp16(std::vector<fp16*>& instances) : instances(instances) { instances.push_back(this); }
	~fp16() {
		if (generated == 2)
			return;
		while (instances.size()) {
			fp16* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	fp16* generate();
};

int fp16::_parent_id = 0;
int fp16::_index_start = 0;



class fp32uvw {
	std::vector<fp32uvw*>& instances;

	int32 value_var;

public:
	bool value_exists = false;

	int32& value() {
		assert_cond(value_exists, "struct field value does not exist");
		return value_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	fp32uvw& operator () () { return *instances.back(); }
	fp32uvw& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	fp32uvw(std::vector<fp32uvw*>& instances) : instances(instances) { instances.push_back(this); }
	~fp32uvw() {
		if (generated == 2)
			return;
		while (instances.size()) {
			fp32uvw* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	fp32uvw* generate();
};

int fp32uvw::_parent_id = 0;
int fp32uvw::_index_start = 0;



class matrix {
	std::vector<matrix*>& instances;

	fp32* a_var;
	fp32* b_var;
	fp32uvw* u_var;
	fp32* c_var;
	fp32* d_var;
	fp32uvw* v_var;
	fp32* x_var;
	fp32* y_var;
	fp32uvw* w_var;

public:
	bool a_exists = false;
	bool b_exists = false;
	bool u_exists = false;
	bool c_exists = false;
	bool d_exists = false;
	bool v_exists = false;
	bool x_exists = false;
	bool y_exists = false;
	bool w_exists = false;

	fp32& a() {
		assert_cond(a_exists, "struct field a does not exist");
		return *a_var;
	}
	fp32& b() {
		assert_cond(b_exists, "struct field b does not exist");
		return *b_var;
	}
	fp32uvw& u() {
		assert_cond(u_exists, "struct field u does not exist");
		return *u_var;
	}
	fp32& c() {
		assert_cond(c_exists, "struct field c does not exist");
		return *c_var;
	}
	fp32& d() {
		assert_cond(d_exists, "struct field d does not exist");
		return *d_var;
	}
	fp32uvw& v() {
		assert_cond(v_exists, "struct field v does not exist");
		return *v_var;
	}
	fp32& x() {
		assert_cond(x_exists, "struct field x does not exist");
		return *x_var;
	}
	fp32& y() {
		assert_cond(y_exists, "struct field y does not exist");
		return *y_var;
	}
	fp32uvw& w() {
		assert_cond(w_exists, "struct field w does not exist");
		return *w_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	matrix& operator () () { return *instances.back(); }
	matrix& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	matrix(std::vector<matrix*>& instances) : instances(instances) { instances.push_back(this); }
	~matrix() {
		if (generated == 2)
			return;
		while (instances.size()) {
			matrix* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	matrix* generate();
};

int matrix::_parent_id = 0;
int matrix::_index_start = 0;



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



class byte_bitfield {
	int small;
	std::vector<byte> known_values;
	byte value;
public:
	byte operator () () { return value; }
	byte_bitfield(int small, std::vector<byte> known_values = {}) : small(small), known_values(known_values) {}

	byte generate(unsigned bits) {
		if (!bits)
			return 0;
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(byte), bits, small);
		} else {
			value = file_acc.file_integer(sizeof(byte), bits, known_values);
		}
		return value;
	}

	byte generate(unsigned bits, std::vector<byte> possible_values) {
		if (!bits)
			return 0;
		value = file_acc.file_integer(sizeof(byte), bits, possible_values);
		return value;
	}
};



class tkhd_flags {
	std::vector<tkhd_flags*>& instances;

	std::vector<byte> dummy_var;
	byte dummy2_var : 4;
	byte track_in_poster_var : 1;
	byte track_in_preview_var : 1;
	byte track_in_movie_var : 1;
	byte track_enabled_var : 1;

public:
	bool dummy_exists = false;
	bool dummy2_exists = false;
	bool track_in_poster_exists = false;
	bool track_in_preview_exists = false;
	bool track_in_movie_exists = false;
	bool track_enabled_exists = false;

	std::vector<byte>& dummy() {
		assert_cond(dummy_exists, "struct field dummy does not exist");
		return dummy_var;
	}
	byte dummy2() {
		assert_cond(dummy2_exists, "struct field dummy2 does not exist");
		return dummy2_var;
	}
	byte track_in_poster() {
		assert_cond(track_in_poster_exists, "struct field track_in_poster does not exist");
		return track_in_poster_var;
	}
	byte track_in_preview() {
		assert_cond(track_in_preview_exists, "struct field track_in_preview does not exist");
		return track_in_preview_var;
	}
	byte track_in_movie() {
		assert_cond(track_in_movie_exists, "struct field track_in_movie does not exist");
		return track_in_movie_var;
	}
	byte track_enabled() {
		assert_cond(track_enabled_exists, "struct field track_enabled does not exist");
		return track_enabled_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	tkhd_flags& operator () () { return *instances.back(); }
	tkhd_flags& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	tkhd_flags(std::vector<tkhd_flags*>& instances) : instances(instances) { instances.push_back(this); }
	~tkhd_flags() {
		if (generated == 2)
			return;
		while (instances.size()) {
			tkhd_flags* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	tkhd_flags* generate();
};

int tkhd_flags::_parent_id = 0;
int tkhd_flags::_index_start = 0;



class uint64_class {
	int small;
	std::vector<uint64> known_values;
	uint64 value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(uint64);
	uint64 operator () () { return value; }
	uint64_class(int small, std::vector<uint64> known_values = {}) : small(small), known_values(known_values) {}

	uint64 generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(uint64), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(uint64), 0, known_values);
		}
		return value;
	}

	uint64 generate(std::vector<uint64> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(uint64), 0, possible_values);
		return value;
	}
};



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



class mp4lang {
	std::vector<mp4lang*>& instances;

	uint16 value_var;

public:
	bool value_exists = false;

	uint16& value() {
		assert_cond(value_exists, "struct field value does not exist");
		return value_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	mp4lang& operator () () { return *instances.back(); }
	mp4lang& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	mp4lang(std::vector<mp4lang*>& instances) : instances(instances) { instances.push_back(this); }
	~mp4lang() {
		if (generated == 2)
			return;
		while (instances.size()) {
			mp4lang* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	mp4lang* generate();
};

int mp4lang::_parent_id = 0;
int mp4lang::_index_start = 0;



class str_stts {
	std::vector<str_stts*>& instances;

	uint32 sample_count_var;
	uint32 sample_delta_var;

public:
	bool sample_count_exists = false;
	bool sample_delta_exists = false;

	uint32& sample_count() {
		assert_cond(sample_count_exists, "struct field sample_count does not exist");
		return sample_count_var;
	}
	uint32& sample_delta() {
		assert_cond(sample_delta_exists, "struct field sample_delta does not exist");
		return sample_delta_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	str_stts& operator () () { return *instances.back(); }
	str_stts& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	str_stts(std::vector<str_stts*>& instances) : instances(instances) { instances.push_back(this); }
	~str_stts() {
		if (generated == 2)
			return;
		while (instances.size()) {
			str_stts* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	str_stts* generate();
};

int str_stts::_parent_id = 0;
int str_stts::_index_start = 0;



class str_stts_array_class {
	str_stts& element;
	std::vector<str_stts*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<str_stts*>& operator () () { return value; }
	str_stts operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	str_stts_array_class(str_stts& element) : element(element) {}

	std::vector<str_stts*> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			value.push_back(element.generate());
			_sizeof += element._sizeof;
		}
		return value;
	}
};



class elst_entry {
	std::vector<elst_entry*>& instances;

	uint32 duration_var;
	uint32 media_time_var;
	fp32* media_rate_var;

public:
	bool duration_exists = false;
	bool media_time_exists = false;
	bool media_rate_exists = false;

	uint32& duration() {
		assert_cond(duration_exists, "struct field duration does not exist");
		return duration_var;
	}
	uint32& media_time() {
		assert_cond(media_time_exists, "struct field media_time does not exist");
		return media_time_var;
	}
	fp32& media_rate() {
		assert_cond(media_rate_exists, "struct field media_rate does not exist");
		return *media_rate_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	elst_entry& operator () () { return *instances.back(); }
	elst_entry& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	elst_entry(std::vector<elst_entry*>& instances) : instances(instances) { instances.push_back(this); }
	~elst_entry() {
		if (generated == 2)
			return;
		while (instances.size()) {
			elst_entry* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	elst_entry* generate();
};

int elst_entry::_parent_id = 0;
int elst_entry::_index_start = 0;



class elst_entry_array_class {
	elst_entry& element;
	std::vector<elst_entry*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<elst_entry*>& operator () () { return value; }
	elst_entry operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	elst_entry_array_class(elst_entry& element) : element(element) {}

	std::vector<elst_entry*> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			value.push_back(element.generate());
			_sizeof += element._sizeof;
		}
		return value;
	}
};



class uint16_array_class {
	uint16_class& element;
	std::unordered_map<int, std::vector<uint16>> element_known_values;
	std::vector<uint16> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<uint16>& operator () () { return value; }
	uint16 operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	uint16_array_class(uint16_class& element, std::unordered_map<int, std::vector<uint16>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}

	std::vector<uint16> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			auto known = element_known_values.find(i);
			if (known == element_known_values.end()) {
				value.push_back(element.generate());
				_sizeof += element._sizeof;
			} else {
				value.push_back(file_acc.file_integer(sizeof(uint16), 0, known->second));
				_sizeof += sizeof(uint16);
			}
		}
		return value;
	}
};



class string_class {
	std::vector<std::string> known_values;
	std::string value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::string operator () () { return value; }
	string_class(std::vector<std::string> known_values = {}) : known_values(known_values) {}

	std::string generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_string();
		} else {
			value = file_acc.file_string(known_values);
		}
		_sizeof = value.length() + 1;
		return value;
	}
};



class vmhd_flags {
	std::vector<vmhd_flags*>& instances;

	std::vector<byte> dummy_var;
	byte dummy2_var;

public:
	bool dummy_exists = false;
	bool dummy2_exists = false;

	std::vector<byte>& dummy() {
		assert_cond(dummy_exists, "struct field dummy does not exist");
		return dummy_var;
	}
	byte& dummy2() {
		assert_cond(dummy2_exists, "struct field dummy2 does not exist");
		return dummy2_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	vmhd_flags& operator () () { return *instances.back(); }
	vmhd_flags& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	vmhd_flags(std::vector<vmhd_flags*>& instances) : instances(instances) { instances.push_back(this); }
	~vmhd_flags() {
		if (generated == 2)
			return;
		while (instances.size()) {
			vmhd_flags* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	vmhd_flags* generate();
};

int vmhd_flags::_parent_id = 0;
int vmhd_flags::_index_start = 0;


qtgfxmode qtgfxmode_generate() {
	return (qtgfxmode) file_acc.file_integer(sizeof(uint16), 0, qtgfxmode_values);
}

qtgfxmode qtgfxmode_generate(std::vector<uint16> known_values) {
	return (qtgfxmode) file_acc.file_integer(sizeof(uint16), 0, known_values);
}


class qtopcolor {
	std::vector<qtopcolor*>& instances;

	uint16 red_var;
	uint16 green_var;
	uint16 blue_var;

public:
	bool red_exists = false;
	bool green_exists = false;
	bool blue_exists = false;

	uint16& red() {
		assert_cond(red_exists, "struct field red does not exist");
		return red_var;
	}
	uint16& green() {
		assert_cond(green_exists, "struct field green does not exist");
		return green_var;
	}
	uint16& blue() {
		assert_cond(blue_exists, "struct field blue does not exist");
		return blue_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	qtopcolor& operator () () { return *instances.back(); }
	qtopcolor& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	qtopcolor(std::vector<qtopcolor*>& instances) : instances(instances) { instances.push_back(this); }
	~qtopcolor() {
		if (generated == 2)
			return;
		while (instances.size()) {
			qtopcolor* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	qtopcolor* generate();
};

int qtopcolor::_parent_id = 0;
int qtopcolor::_index_start = 0;



class uint64_array_class {
	uint64_class& element;
	std::unordered_map<int, std::vector<uint64>> element_known_values;
	std::vector<uint64> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<uint64>& operator () () { return value; }
	uint64 operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	uint64_array_class(uint64_class& element, std::unordered_map<int, std::vector<uint64>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}

	std::vector<uint64> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			auto known = element_known_values.find(i);
			if (known == element_known_values.end()) {
				value.push_back(element.generate());
				_sizeof += element._sizeof;
			} else {
				value.push_back(file_acc.file_integer(sizeof(uint64), 0, known->second));
				_sizeof += sizeof(uint64);
			}
		}
		return value;
	}
};



class KID_struct {
	std::vector<KID_struct*>& instances;

	std::vector<byte> entry_var;

public:
	bool entry_exists = false;

	std::vector<byte>& entry() {
		assert_cond(entry_exists, "struct field entry does not exist");
		return entry_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	KID_struct& operator () () { return *instances.back(); }
	KID_struct& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	KID_struct(std::vector<KID_struct*>& instances) : instances(instances) { instances.push_back(this); }
	~KID_struct() {
		if (generated == 2)
			return;
		while (instances.size()) {
			KID_struct* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	KID_struct* generate();
};

int KID_struct::_parent_id = 0;
int KID_struct::_index_start = 0;



class KID_struct_array_class {
	KID_struct& element;
	std::vector<KID_struct*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<KID_struct*>& operator () () { return value; }
	KID_struct operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	KID_struct_array_class(KID_struct& element) : element(element) {}

	std::vector<KID_struct*> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			value.push_back(element.generate());
			_sizeof += element._sizeof;
		}
		return value;
	}
};



class entry_struct_subsample_data_struct {
	std::vector<entry_struct_subsample_data_struct*>& instances;

	uint16 bytes_of_clear_data_var;
	uint32 bytes_of_protected_data_var;

public:
	bool bytes_of_clear_data_exists = false;
	bool bytes_of_protected_data_exists = false;

	uint16& bytes_of_clear_data() {
		assert_cond(bytes_of_clear_data_exists, "struct field bytes_of_clear_data does not exist");
		return bytes_of_clear_data_var;
	}
	uint32& bytes_of_protected_data() {
		assert_cond(bytes_of_protected_data_exists, "struct field bytes_of_protected_data does not exist");
		return bytes_of_protected_data_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	entry_struct_subsample_data_struct& operator () () { return *instances.back(); }
	entry_struct_subsample_data_struct& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	entry_struct_subsample_data_struct(std::vector<entry_struct_subsample_data_struct*>& instances) : instances(instances) { instances.push_back(this); }
	~entry_struct_subsample_data_struct() {
		if (generated == 2)
			return;
		while (instances.size()) {
			entry_struct_subsample_data_struct* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	entry_struct_subsample_data_struct* generate();
};

int entry_struct_subsample_data_struct::_parent_id = 0;
int entry_struct_subsample_data_struct::_index_start = 0;



class entry_struct_subsample_data_struct_array_class {
	entry_struct_subsample_data_struct& element;
	std::vector<entry_struct_subsample_data_struct*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<entry_struct_subsample_data_struct*>& operator () () { return value; }
	entry_struct_subsample_data_struct operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	entry_struct_subsample_data_struct_array_class(entry_struct_subsample_data_struct& element) : element(element) {}

	std::vector<entry_struct_subsample_data_struct*> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			value.push_back(element.generate());
			_sizeof += element._sizeof;
		}
		return value;
	}
};



class entry_struct {
	std::vector<entry_struct*>& instances;

	std::vector<byte> per_sample_IV_var;
	uint16 subsample_count_var;
	std::vector<entry_struct_subsample_data_struct*> subsample_data_var;

public:
	bool per_sample_IV_exists = false;
	bool subsample_count_exists = false;
	bool subsample_data_exists = false;

	std::vector<byte>& per_sample_IV() {
		assert_cond(per_sample_IV_exists, "struct field per_sample_IV does not exist");
		return per_sample_IV_var;
	}
	uint16& subsample_count() {
		assert_cond(subsample_count_exists, "struct field subsample_count does not exist");
		return subsample_count_var;
	}
	std::vector<entry_struct_subsample_data_struct*>& subsample_data() {
		assert_cond(subsample_data_exists, "struct field subsample_data does not exist");
		return subsample_data_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	entry_struct& operator () () { return *instances.back(); }
	entry_struct& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	entry_struct(std::vector<entry_struct*>& instances) : instances(instances) { instances.push_back(this); }
	~entry_struct() {
		if (generated == 2)
			return;
		while (instances.size()) {
			entry_struct* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	entry_struct* generate();
};

int entry_struct::_parent_id = 0;
int entry_struct::_index_start = 0;



class entry_struct_array_class {
	entry_struct& element;
	std::vector<entry_struct*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<entry_struct*>& operator () () { return value; }
	entry_struct operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	entry_struct_array_class(entry_struct& element) : element(element) {}

	std::vector<entry_struct*> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			value.push_back(element.generate());
			_sizeof += element._sizeof;
		}
		return value;
	}
};



class uint32_array_class {
	uint32_class& element;
	std::unordered_map<int, std::vector<uint32>> element_known_values;
	std::vector<uint32> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<uint32>& operator () () { return value; }
	uint32 operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	uint32_array_class(uint32_class& element, std::unordered_map<int, std::vector<uint32>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}

	std::vector<uint32> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			auto known = element_known_values.find(i);
			if (known == element_known_values.end()) {
				value.push_back(element.generate());
				_sizeof += element._sizeof;
			} else {
				value.push_back(file_acc.file_integer(sizeof(uint32), 0, known->second));
				_sizeof += sizeof(uint32);
			}
		}
		return value;
	}
};



class str_sidx {
	std::vector<str_sidx*>& instances;

	uint32 reference_size31_type1_var;
	uint32 subsegment_duration_var;
	uint32 SAP_delta_time28_type3_starts_with1_var;

public:
	bool reference_size31_type1_exists = false;
	bool subsegment_duration_exists = false;
	bool SAP_delta_time28_type3_starts_with1_exists = false;

	uint32& reference_size31_type1() {
		assert_cond(reference_size31_type1_exists, "struct field reference_size31_type1 does not exist");
		return reference_size31_type1_var;
	}
	uint32& subsegment_duration() {
		assert_cond(subsegment_duration_exists, "struct field subsegment_duration does not exist");
		return subsegment_duration_var;
	}
	uint32& SAP_delta_time28_type3_starts_with1() {
		assert_cond(SAP_delta_time28_type3_starts_with1_exists, "struct field SAP_delta_time28_type3_starts_with1 does not exist");
		return SAP_delta_time28_type3_starts_with1_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	str_sidx& operator () () { return *instances.back(); }
	str_sidx& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	str_sidx(std::vector<str_sidx*>& instances) : instances(instances) { instances.push_back(this); }
	~str_sidx() {
		if (generated == 2)
			return;
		while (instances.size()) {
			str_sidx* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	str_sidx* generate();
};

int str_sidx::_parent_id = 0;
int str_sidx::_index_start = 0;



class str_sidx_array_class {
	str_sidx& element;
	std::vector<str_sidx*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<str_sidx*>& operator () () { return value; }
	str_sidx operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	str_sidx_array_class(str_sidx& element) : element(element) {}

	std::vector<str_sidx*> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			value.push_back(element.generate());
			_sizeof += element._sizeof;
		}
		return value;
	}
};



class mp4box {
	std::vector<mp4box*>& instances;

	uint32 size_var;
	fourcc* type_var;
	mp4box* box_var;
	mp4box* mvhd_block_var;
	mp4box* trak_block_var;
	mp4box* iods_block_var;
	mp4box* udta_block_var;
	mp4box* meta_block_var;
	mp4box* unknown_block_var;
	std::string major_brands_var;
	uint32 major_version_var;
	std::string compatiple_brand_var;
	byte version_var;
	uint32 create_time_var;
	uint32 modify_time_var;
	uint32 time_scale_var;
	uint32 duration_var;
	fp32* preferred_rate_var;
	fp16* preferred_volume_var;
	matrix* matrix_structure_var;
	uint32 preview_time_var;
	uint32 preview_duration_var;
	uint32 poster_time_var;
	uint32 selection_time_var;
	uint32 selection_duration_var;
	uint32 current_time_var;
	uint32 next_track_id_var;
	uint32 length_var;
	std::vector<byte> data_var;
	ubyte n_entries_var;
	std::vector<byte> track_IDs_var;
	mp4box* tkhd_block_var;
	mp4box* mdia_block_var;
	mp4box* tref_block_var;
	mp4box* edts_block_var;
	uint32 track_id_var;
	uint32 duration_tkhd_var;
	uint16 layer_var;
	uint16 alt_group_var;
	fp16* volume_var;
	uint16 reserved3_var;
	mp4box* mdhd_block_var;
	mp4box* hdlr_block_var;
	mp4box* minf_block_var;
	uint16 quality_var;
	uint32 handler_type_var;
	std::vector<byte> rest_var;
	mp4box* elst_block_var;
	mp4box* unkown_block_var;
	mp4box* cprt_block_var;
	std::vector<byte> flag_var;
	mp4box* iinf_block_var;
	mp4box* dinf_block_var;
	mp4box* iloc_block_var;
	mp4box* pitm_block_var;
	mp4box* ipro_block_var;
	mp4box* ipmc_block_var;
	mp4box* xml_block_var;
	mp4box* bxml_block_var;
	mp4box* header_block_var;
	mp4box* stbl_block_var;
	mp4box* co64_block_var;
	mp4box* stco_block_var;
	mp4box* stsc_block_var;
	mp4box* stsz_block_var;
	mp4box* stsd_block_var;
	mp4box* stz2_block_var;
	mp4box* stts_block_var;
	mp4box* ctts_block_var;
	mp4box* stss_block_var;
	mp4box* stsh_block_var;
	mp4box* stdb_block_var;
	mp4box* sdtp_block_var;
	mp4box* sbgp_block_var;
	mp4box* sgpd_block_var;
	mp4box* subs_block_var;
	uint32 entry_count_var;
	mp4box* mixed_box_var;
	uint16 data_reference_index_var;
	uint32 horizresolution_var;
	uint32 vertresolution_var;
	uint16 frame_count_var;
	std::vector<byte> compressorname_var;
	uint16 depth_var;
	mp4box* avcC_box_var;
	mp4box* unknown_box_var;
	byte configurationVersion_var;
	byte AVCProfileIndication_var;
	byte profile_compatibility_var;
	byte AVCLevelIndication_var;
	ubyte reserved_lengthSizeMinusOne_var;
	ubyte reserved_numOfSequenceParameterSets_var;
	uint16 sequenceParameterSetLength_var;
	std::vector<byte> sequenceParameterSetNALUnit_var;
	byte numOfPictureParameterSets_var;
	uint16 pictureParameterSetLength_var;
	std::vector<byte> pictureParameterSetNALUnit_var;
	uint32 reserved_a_var;
	uint16 reserved_b_var;
	uint64 reserved_c_var;
	uint16 channelcount_var;
	uint16 samplesize_var;
	uint16 reserved_d_var;
	uint16 samplerate_tmp_var;
	uint32 samplerate_var;
	mp4box* esds_box_var;
	uint32 sectionID_3_var;
	uint32 data_a_var;
	uint32 sectionID_4_var;
	uint32 data_b_var;
	uint64 reserved_e_var;
	uint32 sectionID_5_var;
	uint32 data_e_var;
	uint16 data_f_var;
	uint32 sectionID_6_var;
	uint32 num_entries_var;
	std::vector<elst_entry*> entries_var;
	std::string notice_var;
	uint16 entry_count_16_tmp_var;
	uint16 entry_count_16_var;
	uint16 item_ID_var;
	uint16 item_protection_index_var;
	std::string item_name_var;
	std::string content_type_var;
	std::string content_encoding_var;
	mp4box* url_box_var;
	mp4box* dref_box_var;
	mp4box* urn_box_var;
	std::string location_var;
	std::string name_var;
	fp16* balance_var;
	uint16 graphics_mode_var;
	qtopcolor* opcolor_var;
	uint32 first_chunk_var;
	uint32 samples_per_chunk_var;
	uint32 sample_description_index_var;
	uint32 sample_size_var;
	uint32 sample_count_var;
	uint32 entry_size_var;
	uint32 codingName_var;
	byte reserved1_var;
	byte default_crypt_skip_byte_block_var;
	byte default_is_protected_var;
	byte default_per_sample_IV_size_var;
	std::vector<byte> default_KID_var;
	byte default_constant_IV_size_var;
	std::vector<byte> default_constant_IV_var;
	uint32 scheme_type_var;
	uint32 scheme_version_var;
	std::vector<byte> systemID_var;
	uint32 KID_count_var;
	std::vector<KID_struct*> KID_var;
	uint32 DataSize_var;
	std::vector<byte> Data_var;
	uint32 aux_info_type_var;
	uint32 aud_info_type_parameter_var;
	uint32 aux_info_type_parameter_var;
	byte default_sample_info_size_var;
	uint32 data_offset_var;
	uint32 first_sample_flags_var;
	uint32 trackID_var;
	uint64 base_data_offset_var;
	uint32 default_sample_duration_var;
	uint32 default_sample_size_var;
	uint32 default_sample_flags_var;
	uint32 sequence_number_var;
	uint32 referenceID_var;
	uint32 timescale_var;
	uint16 reference_count_var;
	std::vector<str_sidx*> references_var;
	uint32 default_sample_description_index_var;
	std::vector<uint32> sample_number_var;
	std::vector<byte> unknown_var;

public:
	bool size_exists = false;
	bool type_exists = false;
	bool box_exists = false;
	bool mvhd_block_exists = false;
	bool trak_block_exists = false;
	bool iods_block_exists = false;
	bool udta_block_exists = false;
	bool meta_block_exists = false;
	bool unknown_block_exists = false;
	bool major_brands_exists = false;
	bool major_version_exists = false;
	bool compatiple_brand_exists = false;
	bool version_exists = false;
	bool create_time_exists = false;
	bool modify_time_exists = false;
	bool time_scale_exists = false;
	bool duration_exists = false;
	bool preferred_rate_exists = false;
	bool preferred_volume_exists = false;
	bool matrix_structure_exists = false;
	bool preview_time_exists = false;
	bool preview_duration_exists = false;
	bool poster_time_exists = false;
	bool selection_time_exists = false;
	bool selection_duration_exists = false;
	bool current_time_exists = false;
	bool next_track_id_exists = false;
	bool length_exists = false;
	bool data_exists = false;
	bool n_entries_exists = false;
	bool track_IDs_exists = false;
	bool tkhd_block_exists = false;
	bool mdia_block_exists = false;
	bool tref_block_exists = false;
	bool edts_block_exists = false;
	bool track_id_exists = false;
	bool duration_tkhd_exists = false;
	bool layer_exists = false;
	bool alt_group_exists = false;
	bool volume_exists = false;
	bool reserved3_exists = false;
	bool mdhd_block_exists = false;
	bool hdlr_block_exists = false;
	bool minf_block_exists = false;
	bool quality_exists = false;
	bool handler_type_exists = false;
	bool rest_exists = false;
	bool elst_block_exists = false;
	bool unkown_block_exists = false;
	bool cprt_block_exists = false;
	bool flag_exists = false;
	bool iinf_block_exists = false;
	bool dinf_block_exists = false;
	bool iloc_block_exists = false;
	bool pitm_block_exists = false;
	bool ipro_block_exists = false;
	bool ipmc_block_exists = false;
	bool xml_block_exists = false;
	bool bxml_block_exists = false;
	bool header_block_exists = false;
	bool stbl_block_exists = false;
	bool co64_block_exists = false;
	bool stco_block_exists = false;
	bool stsc_block_exists = false;
	bool stsz_block_exists = false;
	bool stsd_block_exists = false;
	bool stz2_block_exists = false;
	bool stts_block_exists = false;
	bool ctts_block_exists = false;
	bool stss_block_exists = false;
	bool stsh_block_exists = false;
	bool stdb_block_exists = false;
	bool sdtp_block_exists = false;
	bool sbgp_block_exists = false;
	bool sgpd_block_exists = false;
	bool subs_block_exists = false;
	bool entry_count_exists = false;
	bool mixed_box_exists = false;
	bool data_reference_index_exists = false;
	bool horizresolution_exists = false;
	bool vertresolution_exists = false;
	bool frame_count_exists = false;
	bool compressorname_exists = false;
	bool depth_exists = false;
	bool avcC_box_exists = false;
	bool unknown_box_exists = false;
	bool configurationVersion_exists = false;
	bool AVCProfileIndication_exists = false;
	bool profile_compatibility_exists = false;
	bool AVCLevelIndication_exists = false;
	bool reserved_lengthSizeMinusOne_exists = false;
	bool reserved_numOfSequenceParameterSets_exists = false;
	bool sequenceParameterSetLength_exists = false;
	bool sequenceParameterSetNALUnit_exists = false;
	bool numOfPictureParameterSets_exists = false;
	bool pictureParameterSetLength_exists = false;
	bool pictureParameterSetNALUnit_exists = false;
	bool reserved_a_exists = false;
	bool reserved_b_exists = false;
	bool reserved_c_exists = false;
	bool channelcount_exists = false;
	bool samplesize_exists = false;
	bool reserved_d_exists = false;
	bool samplerate_tmp_exists = false;
	bool samplerate_exists = false;
	bool esds_box_exists = false;
	bool sectionID_3_exists = false;
	bool data_a_exists = false;
	bool sectionID_4_exists = false;
	bool data_b_exists = false;
	bool reserved_e_exists = false;
	bool sectionID_5_exists = false;
	bool data_e_exists = false;
	bool data_f_exists = false;
	bool sectionID_6_exists = false;
	bool num_entries_exists = false;
	bool entries_exists = false;
	bool notice_exists = false;
	bool entry_count_16_tmp_exists = false;
	bool entry_count_16_exists = false;
	bool item_ID_exists = false;
	bool item_protection_index_exists = false;
	bool item_name_exists = false;
	bool content_type_exists = false;
	bool content_encoding_exists = false;
	bool url_box_exists = false;
	bool dref_box_exists = false;
	bool urn_box_exists = false;
	bool location_exists = false;
	bool name_exists = false;
	bool balance_exists = false;
	bool graphics_mode_exists = false;
	bool opcolor_exists = false;
	bool first_chunk_exists = false;
	bool samples_per_chunk_exists = false;
	bool sample_description_index_exists = false;
	bool sample_size_exists = false;
	bool sample_count_exists = false;
	bool entry_size_exists = false;
	bool codingName_exists = false;
	bool reserved1_exists = false;
	bool default_crypt_skip_byte_block_exists = false;
	bool default_is_protected_exists = false;
	bool default_per_sample_IV_size_exists = false;
	bool default_KID_exists = false;
	bool default_constant_IV_size_exists = false;
	bool default_constant_IV_exists = false;
	bool scheme_type_exists = false;
	bool scheme_version_exists = false;
	bool systemID_exists = false;
	bool KID_count_exists = false;
	bool KID_exists = false;
	bool DataSize_exists = false;
	bool Data_exists = false;
	bool aux_info_type_exists = false;
	bool aud_info_type_parameter_exists = false;
	bool aux_info_type_parameter_exists = false;
	bool default_sample_info_size_exists = false;
	bool data_offset_exists = false;
	bool first_sample_flags_exists = false;
	bool trackID_exists = false;
	bool base_data_offset_exists = false;
	bool default_sample_duration_exists = false;
	bool default_sample_size_exists = false;
	bool default_sample_flags_exists = false;
	bool sequence_number_exists = false;
	bool referenceID_exists = false;
	bool timescale_exists = false;
	bool reference_count_exists = false;
	bool references_exists = false;
	bool default_sample_description_index_exists = false;
	bool sample_number_exists = false;
	bool unknown_exists = false;

	uint32& size() {
		assert_cond(size_exists, "struct field size does not exist");
		return size_var;
	}
	fourcc& type() {
		assert_cond(type_exists, "struct field type does not exist");
		return *type_var;
	}
	mp4box& box() {
		assert_cond(box_exists, "struct field box does not exist");
		return *box_var;
	}
	mp4box& mvhd_block() {
		assert_cond(mvhd_block_exists, "struct field mvhd_block does not exist");
		return *mvhd_block_var;
	}
	mp4box& trak_block() {
		assert_cond(trak_block_exists, "struct field trak_block does not exist");
		return *trak_block_var;
	}
	mp4box& iods_block() {
		assert_cond(iods_block_exists, "struct field iods_block does not exist");
		return *iods_block_var;
	}
	mp4box& udta_block() {
		assert_cond(udta_block_exists, "struct field udta_block does not exist");
		return *udta_block_var;
	}
	mp4box& meta_block() {
		assert_cond(meta_block_exists, "struct field meta_block does not exist");
		return *meta_block_var;
	}
	mp4box& unknown_block() {
		assert_cond(unknown_block_exists, "struct field unknown_block does not exist");
		return *unknown_block_var;
	}
	std::string& major_brands() {
		assert_cond(major_brands_exists, "struct field major_brands does not exist");
		return major_brands_var;
	}
	uint32& major_version() {
		assert_cond(major_version_exists, "struct field major_version does not exist");
		return major_version_var;
	}
	std::string& compatiple_brand() {
		assert_cond(compatiple_brand_exists, "struct field compatiple_brand does not exist");
		return compatiple_brand_var;
	}
	byte& version() {
		assert_cond(version_exists, "struct field version does not exist");
		return version_var;
	}
	uint32& create_time() {
		assert_cond(create_time_exists, "struct field create_time does not exist");
		return create_time_var;
	}
	uint32& modify_time() {
		assert_cond(modify_time_exists, "struct field modify_time does not exist");
		return modify_time_var;
	}
	uint32& time_scale() {
		assert_cond(time_scale_exists, "struct field time_scale does not exist");
		return time_scale_var;
	}
	uint32& duration() {
		assert_cond(duration_exists, "struct field duration does not exist");
		return duration_var;
	}
	fp32& preferred_rate() {
		assert_cond(preferred_rate_exists, "struct field preferred_rate does not exist");
		return *preferred_rate_var;
	}
	fp16& preferred_volume() {
		assert_cond(preferred_volume_exists, "struct field preferred_volume does not exist");
		return *preferred_volume_var;
	}
	matrix& matrix_structure() {
		assert_cond(matrix_structure_exists, "struct field matrix_structure does not exist");
		return *matrix_structure_var;
	}
	uint32& preview_time() {
		assert_cond(preview_time_exists, "struct field preview_time does not exist");
		return preview_time_var;
	}
	uint32& preview_duration() {
		assert_cond(preview_duration_exists, "struct field preview_duration does not exist");
		return preview_duration_var;
	}
	uint32& poster_time() {
		assert_cond(poster_time_exists, "struct field poster_time does not exist");
		return poster_time_var;
	}
	uint32& selection_time() {
		assert_cond(selection_time_exists, "struct field selection_time does not exist");
		return selection_time_var;
	}
	uint32& selection_duration() {
		assert_cond(selection_duration_exists, "struct field selection_duration does not exist");
		return selection_duration_var;
	}
	uint32& current_time() {
		assert_cond(current_time_exists, "struct field current_time does not exist");
		return current_time_var;
	}
	uint32& next_track_id() {
		assert_cond(next_track_id_exists, "struct field next_track_id does not exist");
		return next_track_id_var;
	}
	uint32& length() {
		assert_cond(length_exists, "struct field length does not exist");
		return length_var;
	}
	std::vector<byte>& data() {
		assert_cond(data_exists, "struct field data does not exist");
		return data_var;
	}
	ubyte& n_entries() {
		assert_cond(n_entries_exists, "struct field n_entries does not exist");
		return n_entries_var;
	}
	std::vector<byte>& track_IDs() {
		assert_cond(track_IDs_exists, "struct field track_IDs does not exist");
		return track_IDs_var;
	}
	mp4box& tkhd_block() {
		assert_cond(tkhd_block_exists, "struct field tkhd_block does not exist");
		return *tkhd_block_var;
	}
	mp4box& mdia_block() {
		assert_cond(mdia_block_exists, "struct field mdia_block does not exist");
		return *mdia_block_var;
	}
	mp4box& tref_block() {
		assert_cond(tref_block_exists, "struct field tref_block does not exist");
		return *tref_block_var;
	}
	mp4box& edts_block() {
		assert_cond(edts_block_exists, "struct field edts_block does not exist");
		return *edts_block_var;
	}
	uint32& track_id() {
		assert_cond(track_id_exists, "struct field track_id does not exist");
		return track_id_var;
	}
	uint32& duration_tkhd() {
		assert_cond(duration_tkhd_exists, "struct field duration_tkhd does not exist");
		return duration_tkhd_var;
	}
	uint16& layer() {
		assert_cond(layer_exists, "struct field layer does not exist");
		return layer_var;
	}
	uint16& alt_group() {
		assert_cond(alt_group_exists, "struct field alt_group does not exist");
		return alt_group_var;
	}
	fp16& volume() {
		assert_cond(volume_exists, "struct field volume does not exist");
		return *volume_var;
	}
	uint16& reserved3() {
		assert_cond(reserved3_exists, "struct field reserved3 does not exist");
		return reserved3_var;
	}
	mp4box& mdhd_block() {
		assert_cond(mdhd_block_exists, "struct field mdhd_block does not exist");
		return *mdhd_block_var;
	}
	mp4box& hdlr_block() {
		assert_cond(hdlr_block_exists, "struct field hdlr_block does not exist");
		return *hdlr_block_var;
	}
	mp4box& minf_block() {
		assert_cond(minf_block_exists, "struct field minf_block does not exist");
		return *minf_block_var;
	}
	uint16& quality() {
		assert_cond(quality_exists, "struct field quality does not exist");
		return quality_var;
	}
	uint32& handler_type() {
		assert_cond(handler_type_exists, "struct field handler_type does not exist");
		return handler_type_var;
	}
	std::vector<byte>& rest() {
		assert_cond(rest_exists, "struct field rest does not exist");
		return rest_var;
	}
	mp4box& elst_block() {
		assert_cond(elst_block_exists, "struct field elst_block does not exist");
		return *elst_block_var;
	}
	mp4box& unkown_block() {
		assert_cond(unkown_block_exists, "struct field unkown_block does not exist");
		return *unkown_block_var;
	}
	mp4box& cprt_block() {
		assert_cond(cprt_block_exists, "struct field cprt_block does not exist");
		return *cprt_block_var;
	}
	std::vector<byte>& flag() {
		assert_cond(flag_exists, "struct field flag does not exist");
		return flag_var;
	}
	mp4box& iinf_block() {
		assert_cond(iinf_block_exists, "struct field iinf_block does not exist");
		return *iinf_block_var;
	}
	mp4box& dinf_block() {
		assert_cond(dinf_block_exists, "struct field dinf_block does not exist");
		return *dinf_block_var;
	}
	mp4box& iloc_block() {
		assert_cond(iloc_block_exists, "struct field iloc_block does not exist");
		return *iloc_block_var;
	}
	mp4box& pitm_block() {
		assert_cond(pitm_block_exists, "struct field pitm_block does not exist");
		return *pitm_block_var;
	}
	mp4box& ipro_block() {
		assert_cond(ipro_block_exists, "struct field ipro_block does not exist");
		return *ipro_block_var;
	}
	mp4box& ipmc_block() {
		assert_cond(ipmc_block_exists, "struct field ipmc_block does not exist");
		return *ipmc_block_var;
	}
	mp4box& xml_block() {
		assert_cond(xml_block_exists, "struct field xml_block does not exist");
		return *xml_block_var;
	}
	mp4box& bxml_block() {
		assert_cond(bxml_block_exists, "struct field bxml_block does not exist");
		return *bxml_block_var;
	}
	mp4box& header_block() {
		assert_cond(header_block_exists, "struct field header_block does not exist");
		return *header_block_var;
	}
	mp4box& stbl_block() {
		assert_cond(stbl_block_exists, "struct field stbl_block does not exist");
		return *stbl_block_var;
	}
	mp4box& co64_block() {
		assert_cond(co64_block_exists, "struct field co64_block does not exist");
		return *co64_block_var;
	}
	mp4box& stco_block() {
		assert_cond(stco_block_exists, "struct field stco_block does not exist");
		return *stco_block_var;
	}
	mp4box& stsc_block() {
		assert_cond(stsc_block_exists, "struct field stsc_block does not exist");
		return *stsc_block_var;
	}
	mp4box& stsz_block() {
		assert_cond(stsz_block_exists, "struct field stsz_block does not exist");
		return *stsz_block_var;
	}
	mp4box& stsd_block() {
		assert_cond(stsd_block_exists, "struct field stsd_block does not exist");
		return *stsd_block_var;
	}
	mp4box& stz2_block() {
		assert_cond(stz2_block_exists, "struct field stz2_block does not exist");
		return *stz2_block_var;
	}
	mp4box& stts_block() {
		assert_cond(stts_block_exists, "struct field stts_block does not exist");
		return *stts_block_var;
	}
	mp4box& ctts_block() {
		assert_cond(ctts_block_exists, "struct field ctts_block does not exist");
		return *ctts_block_var;
	}
	mp4box& stss_block() {
		assert_cond(stss_block_exists, "struct field stss_block does not exist");
		return *stss_block_var;
	}
	mp4box& stsh_block() {
		assert_cond(stsh_block_exists, "struct field stsh_block does not exist");
		return *stsh_block_var;
	}
	mp4box& stdb_block() {
		assert_cond(stdb_block_exists, "struct field stdb_block does not exist");
		return *stdb_block_var;
	}
	mp4box& sdtp_block() {
		assert_cond(sdtp_block_exists, "struct field sdtp_block does not exist");
		return *sdtp_block_var;
	}
	mp4box& sbgp_block() {
		assert_cond(sbgp_block_exists, "struct field sbgp_block does not exist");
		return *sbgp_block_var;
	}
	mp4box& sgpd_block() {
		assert_cond(sgpd_block_exists, "struct field sgpd_block does not exist");
		return *sgpd_block_var;
	}
	mp4box& subs_block() {
		assert_cond(subs_block_exists, "struct field subs_block does not exist");
		return *subs_block_var;
	}
	uint32& entry_count() {
		assert_cond(entry_count_exists, "struct field entry_count does not exist");
		return entry_count_var;
	}
	mp4box& mixed_box() {
		assert_cond(mixed_box_exists, "struct field mixed_box does not exist");
		return *mixed_box_var;
	}
	uint16& data_reference_index() {
		assert_cond(data_reference_index_exists, "struct field data_reference_index does not exist");
		return data_reference_index_var;
	}
	uint32& horizresolution() {
		assert_cond(horizresolution_exists, "struct field horizresolution does not exist");
		return horizresolution_var;
	}
	uint32& vertresolution() {
		assert_cond(vertresolution_exists, "struct field vertresolution does not exist");
		return vertresolution_var;
	}
	uint16& frame_count() {
		assert_cond(frame_count_exists, "struct field frame_count does not exist");
		return frame_count_var;
	}
	std::vector<byte>& compressorname() {
		assert_cond(compressorname_exists, "struct field compressorname does not exist");
		return compressorname_var;
	}
	uint16& depth() {
		assert_cond(depth_exists, "struct field depth does not exist");
		return depth_var;
	}
	mp4box& avcC_box() {
		assert_cond(avcC_box_exists, "struct field avcC_box does not exist");
		return *avcC_box_var;
	}
	mp4box& unknown_box() {
		assert_cond(unknown_box_exists, "struct field unknown_box does not exist");
		return *unknown_box_var;
	}
	byte& configurationVersion() {
		assert_cond(configurationVersion_exists, "struct field configurationVersion does not exist");
		return configurationVersion_var;
	}
	byte& AVCProfileIndication() {
		assert_cond(AVCProfileIndication_exists, "struct field AVCProfileIndication does not exist");
		return AVCProfileIndication_var;
	}
	byte& profile_compatibility() {
		assert_cond(profile_compatibility_exists, "struct field profile_compatibility does not exist");
		return profile_compatibility_var;
	}
	byte& AVCLevelIndication() {
		assert_cond(AVCLevelIndication_exists, "struct field AVCLevelIndication does not exist");
		return AVCLevelIndication_var;
	}
	ubyte& reserved_lengthSizeMinusOne() {
		assert_cond(reserved_lengthSizeMinusOne_exists, "struct field reserved_lengthSizeMinusOne does not exist");
		return reserved_lengthSizeMinusOne_var;
	}
	ubyte& reserved_numOfSequenceParameterSets() {
		assert_cond(reserved_numOfSequenceParameterSets_exists, "struct field reserved_numOfSequenceParameterSets does not exist");
		return reserved_numOfSequenceParameterSets_var;
	}
	uint16& sequenceParameterSetLength() {
		assert_cond(sequenceParameterSetLength_exists, "struct field sequenceParameterSetLength does not exist");
		return sequenceParameterSetLength_var;
	}
	std::vector<byte>& sequenceParameterSetNALUnit() {
		assert_cond(sequenceParameterSetNALUnit_exists, "struct field sequenceParameterSetNALUnit does not exist");
		return sequenceParameterSetNALUnit_var;
	}
	byte& numOfPictureParameterSets() {
		assert_cond(numOfPictureParameterSets_exists, "struct field numOfPictureParameterSets does not exist");
		return numOfPictureParameterSets_var;
	}
	uint16& pictureParameterSetLength() {
		assert_cond(pictureParameterSetLength_exists, "struct field pictureParameterSetLength does not exist");
		return pictureParameterSetLength_var;
	}
	std::vector<byte>& pictureParameterSetNALUnit() {
		assert_cond(pictureParameterSetNALUnit_exists, "struct field pictureParameterSetNALUnit does not exist");
		return pictureParameterSetNALUnit_var;
	}
	uint32& reserved_a() {
		assert_cond(reserved_a_exists, "struct field reserved_a does not exist");
		return reserved_a_var;
	}
	uint16& reserved_b() {
		assert_cond(reserved_b_exists, "struct field reserved_b does not exist");
		return reserved_b_var;
	}
	uint64& reserved_c() {
		assert_cond(reserved_c_exists, "struct field reserved_c does not exist");
		return reserved_c_var;
	}
	uint16& channelcount() {
		assert_cond(channelcount_exists, "struct field channelcount does not exist");
		return channelcount_var;
	}
	uint16& samplesize() {
		assert_cond(samplesize_exists, "struct field samplesize does not exist");
		return samplesize_var;
	}
	uint16& reserved_d() {
		assert_cond(reserved_d_exists, "struct field reserved_d does not exist");
		return reserved_d_var;
	}
	uint16& samplerate_tmp() {
		assert_cond(samplerate_tmp_exists, "struct field samplerate_tmp does not exist");
		return samplerate_tmp_var;
	}
	uint32& samplerate() {
		assert_cond(samplerate_exists, "struct field samplerate does not exist");
		return samplerate_var;
	}
	mp4box& esds_box() {
		assert_cond(esds_box_exists, "struct field esds_box does not exist");
		return *esds_box_var;
	}
	uint32& sectionID_3() {
		assert_cond(sectionID_3_exists, "struct field sectionID_3 does not exist");
		return sectionID_3_var;
	}
	uint32& data_a() {
		assert_cond(data_a_exists, "struct field data_a does not exist");
		return data_a_var;
	}
	uint32& sectionID_4() {
		assert_cond(sectionID_4_exists, "struct field sectionID_4 does not exist");
		return sectionID_4_var;
	}
	uint32& data_b() {
		assert_cond(data_b_exists, "struct field data_b does not exist");
		return data_b_var;
	}
	uint64& reserved_e() {
		assert_cond(reserved_e_exists, "struct field reserved_e does not exist");
		return reserved_e_var;
	}
	uint32& sectionID_5() {
		assert_cond(sectionID_5_exists, "struct field sectionID_5 does not exist");
		return sectionID_5_var;
	}
	uint32& data_e() {
		assert_cond(data_e_exists, "struct field data_e does not exist");
		return data_e_var;
	}
	uint16& data_f() {
		assert_cond(data_f_exists, "struct field data_f does not exist");
		return data_f_var;
	}
	uint32& sectionID_6() {
		assert_cond(sectionID_6_exists, "struct field sectionID_6 does not exist");
		return sectionID_6_var;
	}
	uint32& num_entries() {
		assert_cond(num_entries_exists, "struct field num_entries does not exist");
		return num_entries_var;
	}
	std::vector<elst_entry*>& entries() {
		assert_cond(entries_exists, "struct field entries does not exist");
		return entries_var;
	}
	std::string& notice() {
		assert_cond(notice_exists, "struct field notice does not exist");
		return notice_var;
	}
	uint16& entry_count_16_tmp() {
		assert_cond(entry_count_16_tmp_exists, "struct field entry_count_16_tmp does not exist");
		return entry_count_16_tmp_var;
	}
	uint16& entry_count_16() {
		assert_cond(entry_count_16_exists, "struct field entry_count_16 does not exist");
		return entry_count_16_var;
	}
	uint16& item_ID() {
		assert_cond(item_ID_exists, "struct field item_ID does not exist");
		return item_ID_var;
	}
	uint16& item_protection_index() {
		assert_cond(item_protection_index_exists, "struct field item_protection_index does not exist");
		return item_protection_index_var;
	}
	std::string& item_name() {
		assert_cond(item_name_exists, "struct field item_name does not exist");
		return item_name_var;
	}
	std::string& content_type() {
		assert_cond(content_type_exists, "struct field content_type does not exist");
		return content_type_var;
	}
	std::string& content_encoding() {
		assert_cond(content_encoding_exists, "struct field content_encoding does not exist");
		return content_encoding_var;
	}
	mp4box& url_box() {
		assert_cond(url_box_exists, "struct field url_box does not exist");
		return *url_box_var;
	}
	mp4box& dref_box() {
		assert_cond(dref_box_exists, "struct field dref_box does not exist");
		return *dref_box_var;
	}
	mp4box& urn_box() {
		assert_cond(urn_box_exists, "struct field urn_box does not exist");
		return *urn_box_var;
	}
	std::string& location() {
		assert_cond(location_exists, "struct field location does not exist");
		return location_var;
	}
	std::string& name() {
		assert_cond(name_exists, "struct field name does not exist");
		return name_var;
	}
	fp16& balance() {
		assert_cond(balance_exists, "struct field balance does not exist");
		return *balance_var;
	}
	uint16& graphics_mode() {
		assert_cond(graphics_mode_exists, "struct field graphics_mode does not exist");
		return graphics_mode_var;
	}
	qtopcolor& opcolor() {
		assert_cond(opcolor_exists, "struct field opcolor does not exist");
		return *opcolor_var;
	}
	uint32& first_chunk() {
		assert_cond(first_chunk_exists, "struct field first_chunk does not exist");
		return first_chunk_var;
	}
	uint32& samples_per_chunk() {
		assert_cond(samples_per_chunk_exists, "struct field samples_per_chunk does not exist");
		return samples_per_chunk_var;
	}
	uint32& sample_description_index() {
		assert_cond(sample_description_index_exists, "struct field sample_description_index does not exist");
		return sample_description_index_var;
	}
	uint32& sample_size() {
		assert_cond(sample_size_exists, "struct field sample_size does not exist");
		return sample_size_var;
	}
	uint32& sample_count() {
		assert_cond(sample_count_exists, "struct field sample_count does not exist");
		return sample_count_var;
	}
	uint32& entry_size() {
		assert_cond(entry_size_exists, "struct field entry_size does not exist");
		return entry_size_var;
	}
	uint32& codingName() {
		assert_cond(codingName_exists, "struct field codingName does not exist");
		return codingName_var;
	}
	byte& reserved1() {
		assert_cond(reserved1_exists, "struct field reserved1 does not exist");
		return reserved1_var;
	}
	byte& default_crypt_skip_byte_block() {
		assert_cond(default_crypt_skip_byte_block_exists, "struct field default_crypt_skip_byte_block does not exist");
		return default_crypt_skip_byte_block_var;
	}
	byte& default_is_protected() {
		assert_cond(default_is_protected_exists, "struct field default_is_protected does not exist");
		return default_is_protected_var;
	}
	byte& default_per_sample_IV_size() {
		assert_cond(default_per_sample_IV_size_exists, "struct field default_per_sample_IV_size does not exist");
		return default_per_sample_IV_size_var;
	}
	std::vector<byte>& default_KID() {
		assert_cond(default_KID_exists, "struct field default_KID does not exist");
		return default_KID_var;
	}
	byte& default_constant_IV_size() {
		assert_cond(default_constant_IV_size_exists, "struct field default_constant_IV_size does not exist");
		return default_constant_IV_size_var;
	}
	std::vector<byte>& default_constant_IV() {
		assert_cond(default_constant_IV_exists, "struct field default_constant_IV does not exist");
		return default_constant_IV_var;
	}
	uint32& scheme_type() {
		assert_cond(scheme_type_exists, "struct field scheme_type does not exist");
		return scheme_type_var;
	}
	uint32& scheme_version() {
		assert_cond(scheme_version_exists, "struct field scheme_version does not exist");
		return scheme_version_var;
	}
	std::vector<byte>& systemID() {
		assert_cond(systemID_exists, "struct field systemID does not exist");
		return systemID_var;
	}
	uint32& KID_count() {
		assert_cond(KID_count_exists, "struct field KID_count does not exist");
		return KID_count_var;
	}
	std::vector<KID_struct*>& KID() {
		assert_cond(KID_exists, "struct field KID does not exist");
		return KID_var;
	}
	uint32& DataSize() {
		assert_cond(DataSize_exists, "struct field DataSize does not exist");
		return DataSize_var;
	}
	std::vector<byte>& Data() {
		assert_cond(Data_exists, "struct field Data does not exist");
		return Data_var;
	}
	uint32& aux_info_type() {
		assert_cond(aux_info_type_exists, "struct field aux_info_type does not exist");
		return aux_info_type_var;
	}
	uint32& aud_info_type_parameter() {
		assert_cond(aud_info_type_parameter_exists, "struct field aud_info_type_parameter does not exist");
		return aud_info_type_parameter_var;
	}
	uint32& aux_info_type_parameter() {
		assert_cond(aux_info_type_parameter_exists, "struct field aux_info_type_parameter does not exist");
		return aux_info_type_parameter_var;
	}
	byte& default_sample_info_size() {
		assert_cond(default_sample_info_size_exists, "struct field default_sample_info_size does not exist");
		return default_sample_info_size_var;
	}
	uint32& data_offset() {
		assert_cond(data_offset_exists, "struct field data_offset does not exist");
		return data_offset_var;
	}
	uint32& first_sample_flags() {
		assert_cond(first_sample_flags_exists, "struct field first_sample_flags does not exist");
		return first_sample_flags_var;
	}
	uint32& trackID() {
		assert_cond(trackID_exists, "struct field trackID does not exist");
		return trackID_var;
	}
	uint64& base_data_offset() {
		assert_cond(base_data_offset_exists, "struct field base_data_offset does not exist");
		return base_data_offset_var;
	}
	uint32& default_sample_duration() {
		assert_cond(default_sample_duration_exists, "struct field default_sample_duration does not exist");
		return default_sample_duration_var;
	}
	uint32& default_sample_size() {
		assert_cond(default_sample_size_exists, "struct field default_sample_size does not exist");
		return default_sample_size_var;
	}
	uint32& default_sample_flags() {
		assert_cond(default_sample_flags_exists, "struct field default_sample_flags does not exist");
		return default_sample_flags_var;
	}
	uint32& sequence_number() {
		assert_cond(sequence_number_exists, "struct field sequence_number does not exist");
		return sequence_number_var;
	}
	uint32& referenceID() {
		assert_cond(referenceID_exists, "struct field referenceID does not exist");
		return referenceID_var;
	}
	uint32& timescale() {
		assert_cond(timescale_exists, "struct field timescale does not exist");
		return timescale_var;
	}
	uint16& reference_count() {
		assert_cond(reference_count_exists, "struct field reference_count does not exist");
		return reference_count_var;
	}
	std::vector<str_sidx*>& references() {
		assert_cond(references_exists, "struct field references does not exist");
		return references_var;
	}
	uint32& default_sample_description_index() {
		assert_cond(default_sample_description_index_exists, "struct field default_sample_description_index does not exist");
		return default_sample_description_index_var;
	}
	std::vector<uint32>& sample_number() {
		assert_cond(sample_number_exists, "struct field sample_number does not exist");
		return sample_number_var;
	}
	std::vector<byte>& unknown() {
		assert_cond(unknown_exists, "struct field unknown does not exist");
		return unknown_var;
	}

	/* locals */
	uint64 startOffset;
	int tries;
	int64 endOffset;
	uint64 contentsize;
	std::string chunk_type;
	std::vector<std::string> preferred_blocks;
	std::vector<std::string> possible_blocks;
	std::vector<std::string> available_major_brands;
	std::string selected_major_brand;
	std::vector<std::string> compatiple_brands;
	std::vector<std::string> preferred_brands;
	std::vector<std::string> possible_brands;
	std::vector<std::string> blocks;
	std::vector<std::string> nextValues;
	uint32 i;
	uint32 tmp;
	byte tmp_masked;
	byte j;
	uint16 tmp_16;
	std::vector<std::string> prefered_blocks;
	uint32 sampleCount;
	uint32 currentIndex;
	int64 before_entry_count;
	int64 after;
	uint32 correct_count;
	int evil;
	uint32 parsedSize;
	uint64 writePosition;
	uint32 newSize;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	mp4box& operator () () { return *instances.back(); }
	mp4box& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	mp4box(std::vector<mp4box*>& instances) : instances(instances) { instances.push_back(this); }
	~mp4box() {
		if (generated == 2)
			return;
		while (instances.size()) {
			mp4box* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	mp4box* generate();
};

int mp4box::_parent_id = 0;
int mp4box::_index_start = 0;



class mp4file {
	std::vector<mp4file*>& instances;

	mp4box* ftyp_block_var;
	mp4box* mdat_block_var;
	mp4box* moov_block_var;
	mp4box* free_block_var;
	mp4box* unknown_block_var;

public:
	bool ftyp_block_exists = false;
	bool mdat_block_exists = false;
	bool moov_block_exists = false;
	bool free_block_exists = false;
	bool unknown_block_exists = false;

	mp4box& ftyp_block() {
		assert_cond(ftyp_block_exists, "struct field ftyp_block does not exist");
		return *ftyp_block_var;
	}
	mp4box& mdat_block() {
		assert_cond(mdat_block_exists, "struct field mdat_block does not exist");
		return *mdat_block_var;
	}
	mp4box& moov_block() {
		assert_cond(moov_block_exists, "struct field moov_block does not exist");
		return *moov_block_var;
	}
	mp4box& free_block() {
		assert_cond(free_block_exists, "struct field free_block does not exist");
		return *free_block_var;
	}
	mp4box& unknown_block() {
		assert_cond(unknown_block_exists, "struct field unknown_block does not exist");
		return *unknown_block_var;
	}

	/* locals */
	std::string chunk_type;
	std::vector<std::string> preferred_blocks;
	std::vector<std::string> possible_blocks;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	mp4file& operator () () { return *instances.back(); }
	mp4file& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	mp4file(std::vector<mp4file*>& instances) : instances(instances) { instances.push_back(this); }
	~mp4file() {
		if (generated == 2)
			return;
		while (instances.size()) {
			mp4file* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	mp4file* generate();
};

int mp4file::_parent_id = 0;
int mp4file::_index_start = 0;

std::vector<byte> ReadByteInitValues;
std::vector<ubyte> ReadUByteInitValues;
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
std::vector<std::string> ReadBytesInitValues = { "avc1", "avcC", "btrt", "bxml", "co64", "cprt", "ctts", "data", "dinf", "dref", "edts", "elst", "enca", "esds", "free", "frma", "ftyp", "hdlr", "hint", "hmhd", "iinf", "iloc", "ilst", "iods", "ipmc", "ipro", "iso2", "isom", "mdat", "mdhd", "mdia", "mehd", "meta", "mfhd", "minf", "mmp4", "moof", "moov", "mp41", "mp42", "mp4a", "mp71", "msnv", "mvex", "mvhd", "ndas", "ndsc", "ndsh", "ndsm", "ndsp", "ndss", "ndxc", "ndxh", "ndxm", "ndxp", "ndxs", "nmhd", "pasp", "pitm", "pssh", "saio", "saiz", "sbgp", "schi", "schm", "sdtp", "senc", "sgpd", "sidx", "sinf", "smhd", "soun", "stbl", "stco", "stdb", "stsc", "stsd", "stsh", "stss", "stsz", "stts", "stz2", "subs", "tenc", "tfhd", "tkhd", "traf", "trak", "tref", "trex", "trun", "udta", "url ", "urn ", "vide", "vmhd", "xml " };


std::vector<fourcc*> fourcc_type_instances;
std::vector<mp4box*> mp4box_box_instances;
std::vector<mp4box*> mp4box_mvhd_block_instances;
std::vector<mp4box*> mp4box_trak_block_instances;
std::vector<mp4box*> mp4box_iods_block_instances;
std::vector<mp4box*> mp4box_udta_block_instances;
std::vector<mp4box*> mp4box_meta_block_instances;
std::vector<mp4box*> mp4box_unknown_block_instances;
std::vector<fp32*> fp32_preferred_rate_instances;
std::vector<fp16*> fp16_preferred_volume_instances;
std::vector<fp32*> fp32_a_instances;
std::vector<fp32*> fp32_b_instances;
std::vector<fp32uvw*> fp32uvw_u_instances;
std::vector<fp32*> fp32_c_instances;
std::vector<fp32*> fp32_d_instances;
std::vector<fp32uvw*> fp32uvw_v_instances;
std::vector<fp32*> fp32_x_instances;
std::vector<fp32*> fp32_y_instances;
std::vector<fp32uvw*> fp32uvw_w_instances;
std::vector<matrix*> matrix_matrix_structure_instances;
std::vector<mp4box*> mp4box_tkhd_block_instances;
std::vector<mp4box*> mp4box_mdia_block_instances;
std::vector<mp4box*> mp4box_tref_block_instances;
std::vector<mp4box*> mp4box_edts_block_instances;
std::vector<tkhd_flags*> tkhd_flags_flags__instances;
std::vector<fp16*> fp16_volume_instances;
std::vector<fp32*> fp32_width_instances;
std::vector<fp32*> fp32_height_instances;
std::vector<mp4box*> mp4box_mdhd_block_instances;
std::vector<mp4box*> mp4box_hdlr_block_instances;
std::vector<mp4box*> mp4box_minf_block_instances;
std::vector<mp4lang*> mp4lang_language_instances;
std::vector<mp4box*> mp4box_elst_block_instances;
std::vector<mp4box*> mp4box_unkown_block_instances;
std::vector<mp4box*> mp4box_cprt_block_instances;
std::vector<mp4box*> mp4box_iinf_block_instances;
std::vector<mp4box*> mp4box_dinf_block_instances;
std::vector<mp4box*> mp4box_iloc_block_instances;
std::vector<mp4box*> mp4box_pitm_block_instances;
std::vector<mp4box*> mp4box_ipro_block_instances;
std::vector<mp4box*> mp4box_ipmc_block_instances;
std::vector<mp4box*> mp4box_xml_block_instances;
std::vector<mp4box*> mp4box_bxml_block_instances;
std::vector<mp4box*> mp4box_header_block_instances;
std::vector<mp4box*> mp4box_stbl_block_instances;
std::vector<mp4box*> mp4box_co64_block_instances;
std::vector<mp4box*> mp4box_stco_block_instances;
std::vector<mp4box*> mp4box_stsc_block_instances;
std::vector<mp4box*> mp4box_stsz_block_instances;
std::vector<mp4box*> mp4box_stsd_block_instances;
std::vector<mp4box*> mp4box_stz2_block_instances;
std::vector<mp4box*> mp4box_stts_block_instances;
std::vector<mp4box*> mp4box_ctts_block_instances;
std::vector<mp4box*> mp4box_stss_block_instances;
std::vector<mp4box*> mp4box_stsh_block_instances;
std::vector<mp4box*> mp4box_stdb_block_instances;
std::vector<mp4box*> mp4box_sdtp_block_instances;
std::vector<mp4box*> mp4box_sbgp_block_instances;
std::vector<mp4box*> mp4box_sgpd_block_instances;
std::vector<mp4box*> mp4box_subs_block_instances;
std::vector<mp4box*> mp4box_mixed_box_instances;
std::vector<mp4box*> mp4box_avcC_box_instances;
std::vector<mp4box*> mp4box_unknown_box_instances;
std::vector<mp4box*> mp4box_esds_box_instances;
std::vector<str_stts*> str_stts_entry_element_instances;
std::vector<fp32*> fp32_media_rate_instances;
std::vector<elst_entry*> elst_entry_entries_element_instances;
std::vector<mp4box*> mp4box_url_box_instances;
std::vector<mp4box*> mp4box_dref_box_instances;
std::vector<mp4box*> mp4box_urn_box_instances;
std::vector<fp16*> fp16_balance_instances;
std::vector<vmhd_flags*> vmhd_flags_flags___instances;
std::vector<qtopcolor*> qtopcolor_opcolor_instances;
std::vector<KID_struct*> KID_struct_KID_element_instances;
std::vector<entry_struct_subsample_data_struct*> entry_struct_subsample_data_struct_subsample_data_element_instances;
std::vector<entry_struct*> entry_struct_entry___element_instances;
std::vector<entry_struct*> entry_struct_entry____instances;
std::vector<str_sidx*> str_sidx_references_element_instances;
std::vector<mp4box*> mp4box_ftyp_block_instances;
std::vector<mp4box*> mp4box_mdat_block_instances;
std::vector<mp4box*> mp4box_moov_block_instances;
std::vector<mp4box*> mp4box_free_block_instances;
std::vector<mp4file*> mp4file_file_instances;


std::unordered_map<std::string, std::string> variable_types = { { "size", "uint32_class" }, { "value", "char_array_class" }, { "type", "fourcc" }, { "box", "mp4box" }, { "mvhd_block", "mp4box" }, { "trak_block", "mp4box" }, { "iods_block", "mp4box" }, { "udta_block", "mp4box" }, { "meta_block", "mp4box" }, { "unknown_block", "mp4box" }, { "major_brands", "char_array_class" }, { "major_version", "uint32_class" }, { "compatiple_brand", "char_array_class" }, { "version", "byte_class" }, { "flags", "byte_array_class" }, { "create_time", "uint32_class" }, { "modify_time", "uint32_class" }, { "time_scale", "uint32_class" }, { "duration", "uint32_class" }, { "value_", "int32_class" }, { "preferred_rate", "fp32" }, { "value__", "int16_class" }, { "preferred_volume", "fp16" }, { "reserved", "byte_array_class" }, { "a", "fp32" }, { "b", "fp32" }, { "u", "fp32uvw" }, { "c", "fp32" }, { "d", "fp32" }, { "v", "fp32uvw" }, { "x", "fp32" }, { "y", "fp32" }, { "w", "fp32uvw" }, { "matrix_structure", "matrix" }, { "preview_time", "uint32_class" }, { "preview_duration", "uint32_class" }, { "poster_time", "uint32_class" }, { "selection_time", "uint32_class" }, { "selection_duration", "uint32_class" }, { "current_time", "uint32_class" }, { "next_track_id", "uint32_class" }, { "length", "uint32_class" }, { "data", "byte_array_class" }, { "n_entries", "ubyte_class" }, { "track_IDs", "byte_array_class" }, { "tkhd_block", "mp4box" }, { "mdia_block", "mp4box" }, { "tref_block", "mp4box" }, { "edts_block", "mp4box" }, { "dummy", "byte_array_class" }, { "dummy2", "byte_bitfield" }, { "track_in_poster", "byte_bitfield" }, { "track_in_preview", "byte_bitfield" }, { "track_in_movie", "byte_bitfield" }, { "track_enabled", "byte_bitfield" }, { "flags_", "tkhd_flags" }, { "track_id", "uint32_class" }, { "reserved_", "uint32_class" }, { "duration_tkhd", "uint32_class" }, { "reserved2", "uint64_class" }, { "layer", "uint16_class" }, { "alt_group", "uint16_class" }, { "volume", "fp16" }, { "reserved3", "uint16_class" }, { "width", "fp32" }, { "height", "fp32" }, { "mdhd_block", "mp4box" }, { "hdlr_block", "mp4box" }, { "minf_block", "mp4box" }, { "value___", "uint16_class" }, { "language", "mp4lang" }, { "quality", "uint16_class" }, { "pre_defined", "uint32_class" }, { "handler_type", "uint32_class" }, { "reserved__", "uint64_class" }, { "rest", "byte_array_class" }, { "elst_block", "mp4box" }, { "unkown_block", "mp4box" }, { "cprt_block", "mp4box" }, { "flag", "byte_array_class" }, { "iinf_block", "mp4box" }, { "dinf_block", "mp4box" }, { "iloc_block", "mp4box" }, { "pitm_block", "mp4box" }, { "ipro_block", "mp4box" }, { "ipmc_block", "mp4box" }, { "xml_block", "mp4box" }, { "bxml_block", "mp4box" }, { "header_block", "mp4box" }, { "stbl_block", "mp4box" }, { "co64_block", "mp4box" }, { "stco_block", "mp4box" }, { "stsc_block", "mp4box" }, { "stsz_block", "mp4box" }, { "stsd_block", "mp4box" }, { "stz2_block", "mp4box" }, { "stts_block", "mp4box" }, { "ctts_block", "mp4box" }, { "stss_block", "mp4box" }, { "stsh_block", "mp4box" }, { "stdb_block", "mp4box" }, { "sdtp_block", "mp4box" }, { "sbgp_block", "mp4box" }, { "sgpd_block", "mp4box" }, { "subs_block", "mp4box" }, { "entry_count", "uint32_class" }, { "mixed_box", "mp4box" }, { "reserved___", "byte_class" }, { "data_reference_index", "uint16_class" }, { "width_", "uint16_class" }, { "height_", "uint16_class" }, { "horizresolution", "uint32_class" }, { "vertresolution", "uint32_class" }, { "frame_count", "uint16_class" }, { "compressorname", "byte_array_class" }, { "depth", "uint16_class" }, { "pre_defined_", "uint16_class" }, { "avcC_box", "mp4box" }, { "unknown_box", "mp4box" }, { "configurationVersion", "byte_class" }, { "AVCProfileIndication", "byte_class" }, { "profile_compatibility", "byte_class" }, { "AVCLevelIndication", "byte_class" }, { "reserved_lengthSizeMinusOne", "ubyte_class" }, { "reserved_numOfSequenceParameterSets", "ubyte_class" }, { "sequenceParameterSetLength", "uint16_class" }, { "sequenceParameterSetNALUnit", "byte_array_class" }, { "numOfPictureParameterSets", "byte_class" }, { "pictureParameterSetLength", "uint16_class" }, { "pictureParameterSetNALUnit", "byte_array_class" }, { "reserved_a", "uint32_class" }, { "reserved_b", "uint16_class" }, { "reserved_c", "uint64_class" }, { "channelcount", "uint16_class" }, { "samplesize", "uint16_class" }, { "reserved_d", "uint16_class" }, { "samplerate_tmp", "uint16_class" }, { "samplerate", "uint32_class" }, { "esds_box", "mp4box" }, { "sectionID_3", "uint32_class" }, { "data_a", "uint32_class" }, { "sectionID_4", "uint32_class" }, { "data_b", "uint32_class" }, { "reserved_e", "uint64_class" }, { "sectionID_5", "uint32_class" }, { "data_e", "uint32_class" }, { "data_f", "uint16_class" }, { "sectionID_6", "uint32_class" }, { "sample_count", "uint32_class" }, { "sample_delta", "uint32_class" }, { "entry", "str_stts_array_class" }, { "num_entries", "uint32_class" }, { "media_time", "uint32_class" }, { "media_rate", "fp32" }, { "entries", "elst_entry_array_class" }, { "language_", "uint16_array_class" }, { "notice", "string_class" }, { "entry_count_16_tmp", "uint16_class" }, { "entry_count_16", "uint16_class" }, { "item_ID", "uint16_class" }, { "item_protection_index", "uint16_class" }, { "item_name", "string_class" }, { "content_type", "string_class" }, { "content_encoding", "string_class" }, { "url_box", "mp4box" }, { "dref_box", "mp4box" }, { "urn_box", "mp4box" }, { "location", "string_class" }, { "name", "string_class" }, { "balance", "fp16" }, { "reserved____", "uint16_class" }, { "dummy2_", "byte_class" }, { "flags__", "vmhd_flags" }, { "graphics_mode", "qtgfxmode" }, { "red", "uint16_class" }, { "green", "uint16_class" }, { "blue", "uint16_class" }, { "opcolor", "qtopcolor" }, { "first_chunk", "uint32_class" }, { "samples_per_chunk", "uint32_class" }, { "sample_description_index", "uint32_class" }, { "chunk_offset", "uint64_array_class" }, { "chunk_offset_", "uint32_class" }, { "sample_size", "uint32_class" }, { "entry_size", "uint32_class" }, { "codingName", "uint32_class" }, { "reserved1", "byte_class" }, { "reserved2_", "byte_class" }, { "default_crypt_skip_byte_block", "byte_class" }, { "default_is_protected", "byte_class" }, { "default_per_sample_IV_size", "byte_class" }, { "default_KID", "byte_array_class" }, { "default_constant_IV_size", "byte_class" }, { "default_constant_IV", "byte_array_class" }, { "scheme_type", "uint32_class" }, { "scheme_version", "uint32_class" }, { "systemID", "byte_array_class" }, { "KID_count", "uint32_class" }, { "entry_", "byte_array_class" }, { "KID", "KID_struct_array_class" }, { "DataSize", "uint32_class" }, { "Data", "byte_array_class" }, { "per_sample_IV", "byte_array_class" }, { "subsample_count", "uint16_class" }, { "bytes_of_clear_data", "uint16_class" }, { "bytes_of_protected_data", "uint32_class" }, { "subsample_data", "entry_struct_subsample_data_struct_array_class" }, { "entry__", "entry_struct_array_class" }, { "aux_info_type", "uint32_class" }, { "aud_info_type_parameter", "uint32_class" }, { "offset", "uint32_array_class" }, { "offset_", "uint64_array_class" }, { "aux_info_type_parameter", "uint32_class" }, { "default_sample_info_size", "byte_class" }, { "data_offset", "uint32_class" }, { "first_sample_flags", "uint32_class" }, { "sample_duration", "uint32_class" }, { "sample_flags", "uint32_class" }, { "sample_composition_time_offset", "uint32_class" }, { "sample_composition_time_offset_", "int32_class" }, { "entry___", "entry_struct" }, { "trackID", "uint32_class" }, { "base_data_offset", "uint64_class" }, { "default_sample_duration", "uint32_class" }, { "default_sample_size", "uint32_class" }, { "default_sample_flags", "uint32_class" }, { "sequence_number", "uint32_class" }, { "referenceID", "uint32_class" }, { "timescale", "uint32_class" }, { "earliest_presentation_time", "uint32_class" }, { "first_offset", "uint32_class" }, { "earliest_presentation_time_", "uint64_class" }, { "first_offset_", "uint64_class" }, { "reference_count", "uint16_class" }, { "reference_size31_type1", "uint32_class" }, { "subsegment_duration", "uint32_class" }, { "SAP_delta_time28_type3_starts_with1", "uint32_class" }, { "references", "str_sidx_array_class" }, { "default_sample_description_index", "uint32_class" }, { "fragment_duration", "uint32_class" }, { "fragment_duration_", "uint64_class" }, { "sample_number", "uint32_array_class" }, { "unknown", "byte_array_class" }, { "ftyp_block", "mp4box" }, { "mdat_block", "mp4box" }, { "moov_block", "mp4box" }, { "free_block", "mp4box" }, { "file", "mp4file" } };

std::vector<std::vector<int>> integer_ranges = { { 1, 16 }, { 3, INT_MAX } };

class globals_class {
public:
	int _struct_id = 0;
	int _struct_id_counter = 0;
	/*local*/ uint32 sharedSamplecountVar;
	/*local*/ uint32 mdatPosition;
	/*local*/ byte isVideo;
	uint32_class size;
	char_class value_element;
	char_array_class value;
	fourcc type;
	mp4box box;
	mp4box mvhd_block;
	mp4box trak_block;
	mp4box iods_block;
	mp4box udta_block;
	mp4box meta_block;
	mp4box unknown_block;
	char_class major_brands_element;
	char_array_class major_brands;
	uint32_class major_version;
	char_class compatiple_brand_element;
	char_array_class compatiple_brand;
	byte_class version;
	byte_class flags_element;
	byte_array_class flags;
	uint32_class create_time;
	uint32_class modify_time;
	uint32_class time_scale;
	uint32_class duration;
	int32_class value_;
	fp32 preferred_rate;
	int16_class value__;
	fp16 preferred_volume;
	byte_class reserved_element;
	byte_array_class reserved;
	fp32 a;
	fp32 b;
	fp32uvw u;
	fp32 c;
	fp32 d;
	fp32uvw v;
	fp32 x;
	fp32 y;
	fp32uvw w;
	matrix matrix_structure;
	uint32_class preview_time;
	uint32_class preview_duration;
	uint32_class poster_time;
	uint32_class selection_time;
	uint32_class selection_duration;
	uint32_class current_time;
	uint32_class next_track_id;
	uint32_class length;
	byte_class data_element;
	byte_array_class data;
	ubyte_class n_entries;
	byte_class track_IDs_element;
	byte_array_class track_IDs;
	mp4box tkhd_block;
	mp4box mdia_block;
	mp4box tref_block;
	mp4box edts_block;
	byte_class dummy_element;
	byte_array_class dummy;
	byte_bitfield dummy2;
	byte_bitfield track_in_poster;
	byte_bitfield track_in_preview;
	byte_bitfield track_in_movie;
	byte_bitfield track_enabled;
	tkhd_flags flags_;
	uint32_class track_id;
	uint32_class reserved_;
	uint32_class duration_tkhd;
	uint64_class reserved2;
	uint16_class layer;
	uint16_class alt_group;
	fp16 volume;
	uint16_class reserved3;
	fp32 width;
	fp32 height;
	mp4box mdhd_block;
	mp4box hdlr_block;
	mp4box minf_block;
	uint16_class value___;
	mp4lang language;
	uint16_class quality;
	uint32_class pre_defined;
	uint32_class handler_type;
	uint64_class reserved__;
	byte_class rest_element;
	byte_array_class rest;
	mp4box elst_block;
	mp4box unkown_block;
	mp4box cprt_block;
	byte_class flag_element;
	byte_array_class flag;
	mp4box iinf_block;
	mp4box dinf_block;
	mp4box iloc_block;
	mp4box pitm_block;
	mp4box ipro_block;
	mp4box ipmc_block;
	mp4box xml_block;
	mp4box bxml_block;
	mp4box header_block;
	mp4box stbl_block;
	mp4box co64_block;
	mp4box stco_block;
	mp4box stsc_block;
	mp4box stsz_block;
	mp4box stsd_block;
	mp4box stz2_block;
	mp4box stts_block;
	mp4box ctts_block;
	mp4box stss_block;
	mp4box stsh_block;
	mp4box stdb_block;
	mp4box sdtp_block;
	mp4box sbgp_block;
	mp4box sgpd_block;
	mp4box subs_block;
	uint32_class entry_count;
	mp4box mixed_box;
	byte_class reserved___;
	uint16_class data_reference_index;
	uint16_class width_;
	uint16_class height_;
	uint32_class horizresolution;
	uint32_class vertresolution;
	uint16_class frame_count;
	byte_class compressorname_element;
	byte_array_class compressorname;
	uint16_class depth;
	uint16_class pre_defined_;
	mp4box avcC_box;
	mp4box unknown_box;
	byte_class configurationVersion;
	byte_class AVCProfileIndication;
	byte_class profile_compatibility;
	byte_class AVCLevelIndication;
	ubyte_class reserved_lengthSizeMinusOne;
	ubyte_class reserved_numOfSequenceParameterSets;
	uint16_class sequenceParameterSetLength;
	byte_class sequenceParameterSetNALUnit_element;
	byte_array_class sequenceParameterSetNALUnit;
	byte_class numOfPictureParameterSets;
	uint16_class pictureParameterSetLength;
	byte_class pictureParameterSetNALUnit_element;
	byte_array_class pictureParameterSetNALUnit;
	uint32_class reserved_a;
	uint16_class reserved_b;
	uint64_class reserved_c;
	uint16_class channelcount;
	uint16_class samplesize;
	uint16_class reserved_d;
	uint16_class samplerate_tmp;
	uint32_class samplerate;
	mp4box esds_box;
	uint32_class sectionID_3;
	uint32_class data_a;
	uint32_class sectionID_4;
	uint32_class data_b;
	uint64_class reserved_e;
	uint32_class sectionID_5;
	uint32_class data_e;
	uint16_class data_f;
	uint32_class sectionID_6;
	uint32_class sample_count;
	uint32_class sample_delta;
	str_stts entry_element;
	str_stts_array_class entry;
	uint32_class num_entries;
	uint32_class media_time;
	fp32 media_rate;
	elst_entry entries_element;
	elst_entry_array_class entries;
	uint16_class language__element;
	uint16_array_class language_;
	string_class notice;
	uint16_class entry_count_16_tmp;
	uint16_class entry_count_16;
	uint16_class item_ID;
	uint16_class item_protection_index;
	string_class item_name;
	string_class content_type;
	string_class content_encoding;
	mp4box url_box;
	mp4box dref_box;
	mp4box urn_box;
	string_class location;
	string_class name;
	fp16 balance;
	uint16_class reserved____;
	byte_class dummy2_;
	vmhd_flags flags__;
	uint16_class red;
	uint16_class green;
	uint16_class blue;
	qtopcolor opcolor;
	uint32_class first_chunk;
	uint32_class samples_per_chunk;
	uint32_class sample_description_index;
	uint64_class chunk_offset_element;
	uint64_array_class chunk_offset;
	uint32_class chunk_offset_;
	uint32_class sample_size;
	uint32_class entry_size;
	uint32_class codingName;
	byte_class reserved1;
	byte_class reserved2_;
	byte_class default_crypt_skip_byte_block;
	byte_class default_is_protected;
	byte_class default_per_sample_IV_size;
	byte_class default_KID_element;
	byte_array_class default_KID;
	byte_class default_constant_IV_size;
	byte_class default_constant_IV_element;
	byte_array_class default_constant_IV;
	uint32_class scheme_type;
	uint32_class scheme_version;
	byte_class systemID_element;
	byte_array_class systemID;
	uint32_class KID_count;
	byte_class entry__element;
	byte_array_class entry_;
	KID_struct KID_element;
	KID_struct_array_class KID;
	uint32_class DataSize;
	byte_class Data_element;
	byte_array_class Data;
	byte_class per_sample_IV_element;
	byte_array_class per_sample_IV;
	uint16_class subsample_count;
	uint16_class bytes_of_clear_data;
	uint32_class bytes_of_protected_data;
	entry_struct_subsample_data_struct subsample_data_element;
	entry_struct_subsample_data_struct_array_class subsample_data;
	entry_struct entry___element;
	entry_struct_array_class entry__;
	uint32_class aux_info_type;
	uint32_class aud_info_type_parameter;
	uint32_class offset_element;
	uint32_array_class offset;
	uint64_class offset__element;
	uint64_array_class offset_;
	uint32_class aux_info_type_parameter;
	byte_class default_sample_info_size;
	uint32_class data_offset;
	uint32_class first_sample_flags;
	uint32_class sample_duration;
	uint32_class sample_flags;
	uint32_class sample_composition_time_offset;
	int32_class sample_composition_time_offset_;
	entry_struct entry___;
	uint32_class trackID;
	uint64_class base_data_offset;
	uint32_class default_sample_duration;
	uint32_class default_sample_size;
	uint32_class default_sample_flags;
	uint32_class sequence_number;
	uint32_class referenceID;
	uint32_class timescale;
	uint32_class earliest_presentation_time;
	uint32_class first_offset;
	uint64_class earliest_presentation_time_;
	uint64_class first_offset_;
	uint16_class reference_count;
	uint32_class reference_size31_type1;
	uint32_class subsegment_duration;
	uint32_class SAP_delta_time28_type3_starts_with1;
	str_sidx references_element;
	str_sidx_array_class references;
	uint32_class default_sample_description_index;
	uint32_class fragment_duration;
	uint64_class fragment_duration_;
	uint32_class sample_number_element;
	uint32_array_class sample_number;
	byte_class unknown_element;
	byte_array_class unknown;
	mp4box ftyp_block;
	mp4box mdat_block;
	mp4box moov_block;
	mp4box free_block;
	mp4file file;


	globals_class() :
		size(1),
		value_element(false),
		value(value_element),
		type(fourcc_type_instances),
		box(mp4box_box_instances),
		mvhd_block(mp4box_mvhd_block_instances),
		trak_block(mp4box_trak_block_instances),
		iods_block(mp4box_iods_block_instances),
		udta_block(mp4box_udta_block_instances),
		meta_block(mp4box_meta_block_instances),
		unknown_block(mp4box_unknown_block_instances),
		major_brands_element(false),
		major_brands(major_brands_element),
		major_version(1),
		compatiple_brand_element(false),
		compatiple_brand(compatiple_brand_element),
		version(1, { 0 }),
		flags_element(false),
		flags(flags_element),
		create_time(1),
		modify_time(1),
		time_scale(1),
		duration(1),
		value_(1),
		preferred_rate(fp32_preferred_rate_instances),
		value__(1),
		preferred_volume(fp16_preferred_volume_instances),
		reserved_element(false),
		reserved(reserved_element),
		a(fp32_a_instances),
		b(fp32_b_instances),
		u(fp32uvw_u_instances),
		c(fp32_c_instances),
		d(fp32_d_instances),
		v(fp32uvw_v_instances),
		x(fp32_x_instances),
		y(fp32_y_instances),
		w(fp32uvw_w_instances),
		matrix_structure(matrix_matrix_structure_instances),
		preview_time(1),
		preview_duration(1),
		poster_time(1),
		selection_time(1),
		selection_duration(1),
		current_time(1),
		next_track_id(1),
		length(2),
		data_element(false),
		data(data_element),
		n_entries(1),
		track_IDs_element(false),
		track_IDs(track_IDs_element),
		tkhd_block(mp4box_tkhd_block_instances),
		mdia_block(mp4box_mdia_block_instances),
		tref_block(mp4box_tref_block_instances),
		edts_block(mp4box_edts_block_instances),
		dummy_element(false),
		dummy(dummy_element),
		dummy2(1),
		track_in_poster(1),
		track_in_preview(1),
		track_in_movie(1),
		track_enabled(1),
		flags_(tkhd_flags_flags__instances),
		track_id(1),
		reserved_(1),
		duration_tkhd(3),
		reserved2(1),
		layer(1),
		alt_group(1),
		volume(fp16_volume_instances),
		reserved3(1),
		width(fp32_width_instances),
		height(fp32_height_instances),
		mdhd_block(mp4box_mdhd_block_instances),
		hdlr_block(mp4box_hdlr_block_instances),
		minf_block(mp4box_minf_block_instances),
		value___(1),
		language(mp4lang_language_instances),
		quality(1),
		pre_defined(1),
		handler_type(1),
		reserved__(1),
		rest_element(false),
		rest(rest_element),
		elst_block(mp4box_elst_block_instances),
		unkown_block(mp4box_unkown_block_instances),
		cprt_block(mp4box_cprt_block_instances),
		flag_element(false),
		flag(flag_element, { { 2, {{2}} } }),
		iinf_block(mp4box_iinf_block_instances),
		dinf_block(mp4box_dinf_block_instances),
		iloc_block(mp4box_iloc_block_instances),
		pitm_block(mp4box_pitm_block_instances),
		ipro_block(mp4box_ipro_block_instances),
		ipmc_block(mp4box_ipmc_block_instances),
		xml_block(mp4box_xml_block_instances),
		bxml_block(mp4box_bxml_block_instances),
		header_block(mp4box_header_block_instances),
		stbl_block(mp4box_stbl_block_instances),
		co64_block(mp4box_co64_block_instances),
		stco_block(mp4box_stco_block_instances),
		stsc_block(mp4box_stsc_block_instances),
		stsz_block(mp4box_stsz_block_instances),
		stsd_block(mp4box_stsd_block_instances),
		stz2_block(mp4box_stz2_block_instances),
		stts_block(mp4box_stts_block_instances),
		ctts_block(mp4box_ctts_block_instances),
		stss_block(mp4box_stss_block_instances),
		stsh_block(mp4box_stsh_block_instances),
		stdb_block(mp4box_stdb_block_instances),
		sdtp_block(mp4box_sdtp_block_instances),
		sbgp_block(mp4box_sbgp_block_instances),
		sgpd_block(mp4box_sgpd_block_instances),
		subs_block(mp4box_subs_block_instances),
		entry_count(1),
		mixed_box(mp4box_mixed_box_instances),
		reserved___(1),
		data_reference_index(1),
		width_(1),
		height_(1),
		horizresolution(1),
		vertresolution(1),
		frame_count(1),
		compressorname_element(false),
		compressorname(compressorname_element),
		depth(1),
		pre_defined_(1),
		avcC_box(mp4box_avcC_box_instances),
		unknown_box(mp4box_unknown_box_instances),
		configurationVersion(1),
		AVCProfileIndication(1),
		profile_compatibility(1),
		AVCLevelIndication(1),
		reserved_lengthSizeMinusOne(1),
		reserved_numOfSequenceParameterSets(1),
		sequenceParameterSetLength(1),
		sequenceParameterSetNALUnit_element(false),
		sequenceParameterSetNALUnit(sequenceParameterSetNALUnit_element),
		numOfPictureParameterSets(1),
		pictureParameterSetLength(1),
		pictureParameterSetNALUnit_element(false),
		pictureParameterSetNALUnit(pictureParameterSetNALUnit_element),
		reserved_a(1),
		reserved_b(1),
		reserved_c(1),
		channelcount(1),
		samplesize(1),
		reserved_d(1),
		samplerate_tmp(1),
		samplerate(1),
		esds_box(mp4box_esds_box_instances),
		sectionID_3(1),
		data_a(1),
		sectionID_4(1),
		data_b(1),
		reserved_e(1),
		sectionID_5(1),
		data_e(1),
		data_f(1),
		sectionID_6(1),
		sample_count(1),
		sample_delta(1),
		entry_element(str_stts_entry_element_instances),
		entry(entry_element),
		num_entries(2),
		media_time(1),
		media_rate(fp32_media_rate_instances),
		entries_element(elst_entry_entries_element_instances),
		entries(entries_element),
		language__element(false),
		language_(language__element),
		entry_count_16_tmp(1),
		entry_count_16(1),
		item_ID(1),
		item_protection_index(1),
		url_box(mp4box_url_box_instances),
		dref_box(mp4box_dref_box_instances),
		urn_box(mp4box_urn_box_instances),
		balance(fp16_balance_instances),
		reserved____(1),
		dummy2_(1),
		flags__(vmhd_flags_flags___instances),
		red(1),
		green(1),
		blue(1),
		opcolor(qtopcolor_opcolor_instances),
		first_chunk(1),
		samples_per_chunk(1),
		sample_description_index(1),
		chunk_offset_element(false),
		chunk_offset(chunk_offset_element),
		chunk_offset_(1),
		sample_size(1),
		entry_size(1),
		codingName(1),
		reserved1(1),
		reserved2_(1),
		default_crypt_skip_byte_block(1),
		default_is_protected(1),
		default_per_sample_IV_size(1, { 0 }),
		default_KID_element(false),
		default_KID(default_KID_element),
		default_constant_IV_size(1),
		default_constant_IV_element(false),
		default_constant_IV(default_constant_IV_element),
		scheme_type(1),
		scheme_version(1),
		systemID_element(false),
		systemID(systemID_element),
		KID_count(1),
		entry__element(false),
		entry_(entry__element),
		KID_element(KID_struct_KID_element_instances),
		KID(KID_element),
		DataSize(1),
		Data_element(false),
		Data(Data_element),
		per_sample_IV_element(false),
		per_sample_IV(per_sample_IV_element),
		subsample_count(1),
		bytes_of_clear_data(1),
		bytes_of_protected_data(1),
		subsample_data_element(entry_struct_subsample_data_struct_subsample_data_element_instances),
		subsample_data(subsample_data_element),
		entry___element(entry_struct_entry___element_instances),
		entry__(entry___element),
		aux_info_type(1),
		aud_info_type_parameter(1),
		offset_element(false),
		offset(offset_element),
		offset__element(false),
		offset_(offset__element),
		aux_info_type_parameter(1),
		default_sample_info_size(1, { 0 }),
		data_offset(1),
		first_sample_flags(1),
		sample_duration(1),
		sample_flags(1),
		sample_composition_time_offset(1),
		sample_composition_time_offset_(1),
		entry___(entry_struct_entry____instances),
		trackID(1),
		base_data_offset(1),
		default_sample_duration(1),
		default_sample_size(1),
		default_sample_flags(1),
		sequence_number(1),
		referenceID(1),
		timescale(1),
		earliest_presentation_time(1),
		first_offset(1),
		earliest_presentation_time_(1),
		first_offset_(1),
		reference_count(1),
		reference_size31_type1(1),
		subsegment_duration(1),
		SAP_delta_time28_type3_starts_with1(1),
		references_element(str_sidx_references_element_instances),
		references(references_element),
		default_sample_description_index(1),
		fragment_duration(1),
		fragment_duration_(1),
		sample_number_element(false),
		sample_number(sample_number_element),
		unknown_element(false),
		unknown(unknown_element),
		ftyp_block(mp4box_ftyp_block_instances),
		mdat_block(mp4box_mdat_block_instances),
		moov_block(mp4box_moov_block_instances),
		free_block(mp4box_free_block_instances),
		file(mp4file_file_instances)
	{}
};

globals_class* g;


fourcc* fourcc::generate() {
	if (generated == 1) {
		fourcc* new_instance = new fourcc(instances);
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

	GENERATE_VAR(value, ::g->value.generate(4, { "dinf", "edts", "mdia", "minf", "moov", "moof", "stbl", "trak", "udta", "traf", "mvex", "sinf", "schi", "frma", "tenc", "schm", "pssh", "senc", "saio", "saiz", "trun", "tfhd", "mfhd", "sidx", "trex", "mehd", "stsd", "enca", "stts", "stsc", "stco", "co64", "stsz", "stss", "elst", "ftyp", "hdlr", "mdhd", "mvhd", "smhd", "tkhd", "vmhd", "data", "free" }));

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


fp32* fp32::generate() {
	if (generated == 1) {
		fp32* new_instance = new fp32(instances);
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

	GENERATE_VAR(value, ::g->value_.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


fp16* fp16::generate() {
	if (generated == 1) {
		fp16* new_instance = new fp16(instances);
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

	GENERATE_VAR(value, ::g->value__.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


fp32uvw* fp32uvw::generate() {
	if (generated == 1) {
		fp32uvw* new_instance = new fp32uvw(instances);
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

	GENERATE_VAR(value, ::g->value_.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


matrix* matrix::generate() {
	if (generated == 1) {
		matrix* new_instance = new matrix(instances);
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

	GENERATE_VAR(a, ::g->a.generate());
	GENERATE_VAR(b, ::g->b.generate());
	GENERATE_VAR(u, ::g->u.generate());
	GENERATE_VAR(c, ::g->c.generate());
	GENERATE_VAR(d, ::g->d.generate());
	GENERATE_VAR(v, ::g->v.generate());
	GENERATE_VAR(x, ::g->x.generate());
	GENERATE_VAR(y, ::g->y.generate());
	GENERATE_VAR(w, ::g->w.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


tkhd_flags* tkhd_flags::generate() {
	if (generated == 1) {
		tkhd_flags* new_instance = new tkhd_flags(instances);
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

	GENERATE_VAR(dummy, ::g->dummy.generate(2));
	GENERATE_VAR(dummy2, ::g->dummy2.generate(4));
	GENERATE_VAR(track_in_poster, ::g->track_in_poster.generate(1));
	GENERATE_VAR(track_in_preview, ::g->track_in_preview.generate(1));
	GENERATE_VAR(track_in_movie, ::g->track_in_movie.generate(1));
	GENERATE_VAR(track_enabled, ::g->track_enabled.generate(1));

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


mp4lang* mp4lang::generate() {
	if (generated == 1) {
		mp4lang* new_instance = new mp4lang(instances);
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

	GENERATE_VAR(value, ::g->value___.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


str_stts* str_stts::generate() {
	if (generated == 1) {
		str_stts* new_instance = new str_stts(instances);
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

	GENERATE_VAR(sample_count, ::g->sample_count.generate());
	GENERATE_VAR(sample_delta, ::g->sample_delta.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


elst_entry* elst_entry::generate() {
	if (generated == 1) {
		elst_entry* new_instance = new elst_entry(instances);
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

	GENERATE_VAR(duration, ::g->duration.generate());
	GENERATE_VAR(media_time, ::g->media_time.generate());
	GENERATE_VAR(media_rate, ::g->media_rate.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


vmhd_flags* vmhd_flags::generate() {
	if (generated == 1) {
		vmhd_flags* new_instance = new vmhd_flags(instances);
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

	GENERATE_VAR(dummy, ::g->dummy.generate(2));
	GENERATE_VAR(dummy2, ::g->dummy2_.generate({ 1 }));

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


qtopcolor* qtopcolor::generate() {
	if (generated == 1) {
		qtopcolor* new_instance = new qtopcolor(instances);
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

	GENERATE_VAR(red, ::g->red.generate());
	GENERATE_VAR(green, ::g->green.generate());
	GENERATE_VAR(blue, ::g->blue.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


KID_struct* KID_struct::generate() {
	if (generated == 1) {
		KID_struct* new_instance = new KID_struct(instances);
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

	GENERATE_VAR(entry, ::g->entry_.generate(16));

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


entry_struct_subsample_data_struct* entry_struct_subsample_data_struct::generate() {
	if (generated == 1) {
		entry_struct_subsample_data_struct* new_instance = new entry_struct_subsample_data_struct(instances);
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

	GENERATE_VAR(bytes_of_clear_data, ::g->bytes_of_clear_data.generate());
	GENERATE_VAR(bytes_of_protected_data, ::g->bytes_of_protected_data.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


entry_struct* entry_struct::generate() {
	if (generated == 1) {
		entry_struct* new_instance = new entry_struct(instances);
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

	GENERATE_VAR(per_sample_IV, ::g->per_sample_IV.generate(8));
	if ((::g->flag()[2] == 2)) {
		GENERATE_VAR(subsample_count, ::g->subsample_count.generate());
		GENERATE_VAR(subsample_data, ::g->subsample_data.generate(subsample_count()));
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


str_sidx* str_sidx::generate() {
	if (generated == 1) {
		str_sidx* new_instance = new str_sidx(instances);
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

	GENERATE_VAR(reference_size31_type1, ::g->reference_size31_type1.generate());
	GENERATE_VAR(subsegment_duration, ::g->subsegment_duration.generate());
	GENERATE_VAR(SAP_delta_time28_type3_starts_with1, ::g->SAP_delta_time28_type3_starts_with1.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


mp4box* mp4box::generate() {
	if (generated == 1) {
		mp4box* new_instance = new mp4box(instances);
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

	startOffset = FTell();
	tries = 0;
	for (tries = 0; (tries < 3); ++tries) {
			FSeek(startOffset);
		GENERATE_VAR(size, ::g->size.generate({ 0 }));
		if (!size()) {
		break;
		};
	;
	};
	GENERATE_VAR(type, ::g->type.generate());
	endOffset = (startOffset + size());
	contentsize = (size() - 8);
	switch (STR2INT(type().value())) {
	case STR2INT("moof"):
	case STR2INT("traf"):
	case STR2INT("mvex"):
	case STR2INT("sinf"):
	case STR2INT("schi"):
		while ((FTell() < endOffset)) {
			GENERATE_VAR(box, ::g->box.generate());
			FSeek(box().endOffset);
		};
		break;
	case STR2INT("moov"):
		chunk_type.resize(4);
		preferred_blocks = { "mvhd", "trak" };
		possible_blocks = { "mvhd", "trak", "udta" };
		while (ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks)) {
			switch (STR2INT(chunk_type)) {
			case STR2INT("mvhd"):
				GENERATE_VAR(mvhd_block, ::g->mvhd_block.generate());
				VectorRemove(preferred_blocks, { "mvhd" });
				VectorRemove(possible_blocks, { "mvhd" });
				break;
			case STR2INT("trak"):
				GENERATE_VAR(trak_block, ::g->trak_block.generate());
				VectorRemove(preferred_blocks, { "trak" });
				break;
			case STR2INT("iods"):
				GENERATE_VAR(iods_block, ::g->iods_block.generate());
				break;
			case STR2INT("udta"):
				GENERATE_VAR(udta_block, ::g->udta_block.generate());
				break;
			case STR2INT("meta"):
				GENERATE_VAR(meta_block, ::g->meta_block.generate());
				break;
			default:
				GENERATE_VAR(unknown_block, ::g->unknown_block.generate());
				break;
			};
			if (((startOffset + size()) == (uint64)FTell())) {
				break;
			};
		};
		break;
	case STR2INT("ftyp"):
		available_major_brands = { "avc1", "iso2", "isom", "mmp4", "mp41", "mp42", "mp71", "msnv", "ndas", "ndsc", "ndsh", "ndsm", "ndsp", "ndss", "ndxc", "ndxh", "ndxm", "ndxp", "ndxs" };
		selected_major_brand.resize(4);
		ReadBytes(selected_major_brand, FTell(), 4, available_major_brands);
		GENERATE_VAR(major_brands, ::g->major_brands.generate(4));
		chunk_type.resize(4);
		if ((selected_major_brand == "isom")) {
			::g->isVideo = true;
			GENERATE_VAR(major_version, ::g->major_version.generate({ 512 }));
			compatiple_brands = { "isom", "iso2", "avc1", "mp41" };
			while (ReadBytes(chunk_type, FTell(), 4, compatiple_brands, compatiple_brands, 0.99)) {
				GENERATE_VAR(compatiple_brand, ::g->compatiple_brand.generate(4));
				VectorRemove(compatiple_brands, { chunk_type });
				if (((startOffset + size()) == (uint64)FTell())) {
					break;
				};
			};
		} else {
			::g->isVideo = false;
			GENERATE_VAR(major_version, ::g->major_version.generate());
			preferred_brands = { selected_major_brand };
			possible_brands = { "avc1", "iso2", "isom", "mmp4", "mp41", "mp42", "mp71", "msnv", "ndas", "ndsc", "ndsh", "ndsm", "ndsp", "ndss", "ndxc", "ndxh", "ndxm", "ndxp", "ndxs" };
			while (ReadBytes(chunk_type, FTell(), 4, preferred_brands, possible_brands)) {
				GENERATE_VAR(compatiple_brand, ::g->compatiple_brand.generate(4));
				if ((chunk_type == selected_major_brand)) {
					preferred_brands = {  };
				};
				if (((startOffset + size()) == (uint64)FTell())) {
					break;
				};
			};
		};
		break;
	case STR2INT("mvhd"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE(flags, ::g->flags.generate(3));
		GENERATE_VAR(create_time, ::g->create_time.generate());
		GENERATE_VAR(modify_time, ::g->modify_time.generate());
		GENERATE_VAR(time_scale, ::g->time_scale.generate());
		GENERATE_VAR(duration, ::g->duration.generate());
		GENERATE_VAR(preferred_rate, ::g->preferred_rate.generate());
		GENERATE_VAR(preferred_volume, ::g->preferred_volume.generate());
		GENERATE(reserved, ::g->reserved.generate(10));
		GENERATE_VAR(matrix_structure, ::g->matrix_structure.generate());
		GENERATE_VAR(preview_time, ::g->preview_time.generate());
		GENERATE_VAR(preview_duration, ::g->preview_duration.generate());
		GENERATE_VAR(poster_time, ::g->poster_time.generate());
		GENERATE_VAR(selection_time, ::g->selection_time.generate());
		GENERATE_VAR(selection_duration, ::g->selection_duration.generate());
		GENERATE_VAR(current_time, ::g->current_time.generate());
		GENERATE_VAR(next_track_id, ::g->next_track_id.generate());
		break;
	case STR2INT("mdat"):
		::g->mdatPosition = FTell();
		if ((size() < 8)) {
			GENERATE_VAR(length, ::g->length.generate());
			GENERATE_VAR(data, ::g->data.generate(length()));
		} else {
			GENERATE_VAR(data, ::g->data.generate((size() - 8)));
		};
		break;
	case STR2INT("iods"):
		if ((size() < 1)) {
			GENERATE_VAR(n_entries, ::g->n_entries.generate());
			FSeek((FTell() - 1));
			GENERATE_VAR(track_IDs, ::g->track_IDs.generate(n_entries()));
		} else {
			GENERATE_VAR(track_IDs, ::g->track_IDs.generate((size() - 8)));
		};
		break;
	case STR2INT("tref"):
		if ((size() < 1)) {
			GENERATE_VAR(n_entries, ::g->n_entries.generate());
			FSeek((FTell() - 1));
			GENERATE_VAR(track_IDs, ::g->track_IDs.generate(n_entries()));
		} else {
			GENERATE_VAR(track_IDs, ::g->track_IDs.generate((size() - 8)));
		};
		break;
	case STR2INT("trak"):
		chunk_type.resize(4);
		preferred_blocks = { "tkhd", "mdia" };
		possible_blocks = { "tkhd", "mdia" };
		while (ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks)) {
			switch (STR2INT(chunk_type)) {
			case STR2INT("tkhd"):
				GENERATE_VAR(tkhd_block, ::g->tkhd_block.generate());
				VectorRemove(preferred_blocks, { "tkhd" });
				break;
			case STR2INT("mdia"):
				GENERATE_VAR(mdia_block, ::g->mdia_block.generate());
				VectorRemove(preferred_blocks, { "mdia" });
				break;
			case STR2INT("meta"):
				GENERATE_VAR(meta_block, ::g->meta_block.generate());
				break;
			case STR2INT("tref"):
				GENERATE_VAR(tref_block, ::g->tref_block.generate());
				break;
			case STR2INT("edts"):
				GENERATE_VAR(edts_block, ::g->edts_block.generate());
				break;
			case STR2INT("udta"):
				GENERATE_VAR(udta_block, ::g->udta_block.generate());
				break;
			default:
				GENERATE_VAR(unknown_block, ::g->unknown_block.generate());
				break;
			};
			VectorRemove(possible_blocks, { chunk_type });
			if (((startOffset + size()) == (uint64)FTell())) {
				break;
			};
		};
		break;
	case STR2INT("tkhd"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE(flags, ::g->flags_.generate());
		GENERATE_VAR(create_time, ::g->create_time.generate());
		GENERATE_VAR(modify_time, ::g->modify_time.generate());
		GENERATE_VAR(track_id, ::g->track_id.generate());
		GENERATE(reserved, ::g->reserved_.generate());
		GENERATE_VAR(duration_tkhd, ::g->duration_tkhd.generate());
		GENERATE(reserved2, ::g->reserved2.generate());
		GENERATE_VAR(layer, ::g->layer.generate());
		GENERATE_VAR(alt_group, ::g->alt_group.generate());
		GENERATE_VAR(volume, ::g->volume.generate());
		GENERATE_VAR(reserved3, ::g->reserved3.generate());
		GENERATE_VAR(matrix_structure, ::g->matrix_structure.generate());
		GENERATE(width, ::g->width.generate());
		GENERATE(height, ::g->height.generate());
		break;
	case STR2INT("mdia"):
		chunk_type.resize(4);
		preferred_blocks = { "mdhd", "hdlr", "minf" };
		possible_blocks = { "mdhd", "hdlr", "minf" };
		while (ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks)) {
			switch (STR2INT(chunk_type)) {
			case STR2INT("mdhd"):
				GENERATE_VAR(mdhd_block, ::g->mdhd_block.generate());
				break;
			case STR2INT("hdlr"):
				GENERATE_VAR(hdlr_block, ::g->hdlr_block.generate());
				break;
			case STR2INT("minf"):
				GENERATE_VAR(minf_block, ::g->minf_block.generate());
				break;
			default:
				GENERATE_VAR(unknown_block, ::g->unknown_block.generate());
				break;
			};
			VectorRemove(preferred_blocks, { chunk_type });
			VectorRemove(possible_blocks, { chunk_type });
			if (((startOffset + size()) == (uint64)FTell())) {
				break;
			};
		};
		break;
	case STR2INT("mdhd"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE(flags, ::g->flags.generate(3));
		GENERATE_VAR(create_time, ::g->create_time.generate());
		GENERATE_VAR(modify_time, ::g->modify_time.generate());
		GENERATE_VAR(time_scale, ::g->time_scale.generate());
		GENERATE_VAR(duration, ::g->duration.generate());
		GENERATE(language, ::g->language.generate());
		GENERATE_VAR(quality, ::g->quality.generate());
		break;
	case STR2INT("hdlr"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE(flags, ::g->flags.generate(3));
		GENERATE(pre_defined, ::g->pre_defined.generate({ 0 }));
		if (::g->isVideo) {
			GENERATE_VAR(handler_type, ::g->handler_type.generate({ 0x76696465 }));
			GENERATE(reserved, ::g->reserved__.generate({ 0x6170706C00000000 }));
		} else {
			GENERATE_VAR(handler_type, ::g->handler_type.generate({ 1936684398 }));
			GENERATE(reserved, ::g->reserved__.generate({ 0 }));
		};
		if ((size() > (FTell() - startOffset))) {
			GENERATE_VAR(rest, ::g->rest.generate((size() - (FTell() - startOffset))));
		} else {
			GENERATE_VAR(rest, ::g->rest.generate(17));
		};
		break;
	case STR2INT("edts"):
		chunk_type.resize(4);
		preferred_blocks = { "elst" };
		possible_blocks = { "elst" };
		if (((startOffset + size()) == (uint64)FTell())) {
			break;
		};
		if (ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks)) {
			if ((chunk_type == "elst")) {
				GENERATE_VAR(elst_block, ::g->elst_block.generate());
			} else {
				GENERATE_VAR(unknown_block, ::g->unknown_block.generate());
			};
		};
		break;
	case STR2INT("udta"):
		chunk_type.resize(4);
		if (::g->isVideo) {
			blocks = { "meta" };
			if (ReadBytes(chunk_type, (FTell() + 4), 4, blocks, blocks)) {
				switch (STR2INT(chunk_type)) {
				case STR2INT("meta"):
					GENERATE_VAR(meta_block, ::g->meta_block.generate());
					VectorRemove(blocks, { chunk_type });
					break;
				default:
					GENERATE_VAR(unkown_block, ::g->unkown_block.generate());
					break;
				};
			};
		} else {
			preferred_blocks = { "cprt" };
			possible_blocks = { "cprt" };
			if (ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks)) {
				if ((chunk_type == "cprt")) {
					GENERATE_VAR(cprt_block, ::g->cprt_block.generate());
				} else {
					GENERATE_VAR(unkown_block, ::g->unkown_block.generate());
				};
			};
		};
		break;
	case STR2INT("meta"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		chunk_type.resize(4);
		preferred_blocks = { "hdlr" };
		possible_blocks = { "hdlr" };
		while (ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks)) {
			switch (STR2INT(chunk_type)) {
			case STR2INT("hdlr"):
				GENERATE_VAR(hdlr_block, ::g->hdlr_block.generate());
				VectorRemove(preferred_blocks, { "hdlr" });
				break;
			case STR2INT("iinf"):
				GENERATE_VAR(iinf_block, ::g->iinf_block.generate());
				break;
			case STR2INT("dinf"):
				GENERATE_VAR(dinf_block, ::g->dinf_block.generate());
				break;
			case STR2INT("iloc"):
				GENERATE_VAR(iloc_block, ::g->iloc_block.generate());
				break;
			case STR2INT("pitm"):
				GENERATE_VAR(pitm_block, ::g->pitm_block.generate());
				break;
			case STR2INT("ipro"):
				GENERATE_VAR(ipro_block, ::g->ipro_block.generate());
				break;
			case STR2INT("ipmc"):
				GENERATE_VAR(ipmc_block, ::g->ipmc_block.generate());
				break;
			case STR2INT("xml "):
				GENERATE_VAR(xml_block, ::g->xml_block.generate());
				break;
			case STR2INT("bxml"):
				GENERATE_VAR(bxml_block, ::g->bxml_block.generate());
				break;
			default:
				GENERATE_VAR(unknown_block, ::g->unknown_block.generate());
				break;
			};
			VectorRemove(possible_blocks, { chunk_type });
			if (((startOffset + size()) == (uint64)FTell())) {
				break;
			};
		};
		break;
	case STR2INT("minf"):
		chunk_type.resize(4);
		if (::g->isVideo) {
			preferred_blocks = { "vmhd", "dinf", "stbl" };
			possible_blocks = { "vmhd", "dinf", "stbl" };
		} else {
			preferred_blocks = { "smhd", "dinf", "stbl" };
			possible_blocks = { "smhd", "dinf", "stbl" };
		};
		while (ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks)) {
			switch (STR2INT(chunk_type)) {
			case STR2INT("vmhd"):
			case STR2INT("smhd"):
			case STR2INT("hmhd"):
			case STR2INT("nmhd"):
				GENERATE_VAR(header_block, ::g->header_block.generate());
				VectorRemove(preferred_blocks, { "vmhd", "smhd", "hmhd", "nmhd" });
				VectorRemove(possible_blocks, { "vmhd", "smhd", "hmhd", "nmhd" });
				break;
			case STR2INT("stbl"):
				GENERATE_VAR(stbl_block, ::g->stbl_block.generate());
				VectorRemove(preferred_blocks, { chunk_type });
				VectorRemove(possible_blocks, { chunk_type });
				break;
			case STR2INT("dinf"):
				GENERATE_VAR(dinf_block, ::g->dinf_block.generate());
				VectorRemove(preferred_blocks, { chunk_type });
				VectorRemove(possible_blocks, { chunk_type });
				break;
			default:
				GENERATE_VAR(unknown_block, ::g->unknown_block.generate());
				break;
			};
			if (((startOffset + size()) == (uint64)FTell())) {
				break;
			};
		};
		break;
	case STR2INT("stbl"):
		chunk_type.resize(4);
		preferred_blocks = { "stts", "stsd", "stsc", "stco" };
		possible_blocks = { "stts", "stsd", "stsc", "stco", "stss" };
		while (ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks)) {
			switch (STR2INT(chunk_type)) {
			case STR2INT("co64"):
				GENERATE_VAR(co64_block, ::g->co64_block.generate());
				VectorRemove(preferred_blocks, { "co64", "stco" });
				VectorRemove(possible_blocks, { "co64", "stco" });
				break;
			case STR2INT("stco"):
				GENERATE_VAR(stco_block, ::g->stco_block.generate());
				VectorRemove(preferred_blocks, { "co64", "stco" });
				VectorRemove(possible_blocks, { "co64", "stco" });
				break;
			case STR2INT("stsc"):
				GENERATE_VAR(stsc_block, ::g->stsc_block.generate());
				VectorRemove(preferred_blocks, { "stsc", "stsz", "stz2" });
				VectorRemove(possible_blocks, { "stsc", "stsz", "stz2" });
				nextValues = { "stsz" };
				ReadBytes(chunk_type, (FTell() + 4), 4, nextValues, nextValues);
				GENERATE_VAR(stsz_block, ::g->stsz_block.generate());
				break;
			case STR2INT("stsd"):
				GENERATE_VAR(stsd_block, ::g->stsd_block.generate());
				VectorRemove(preferred_blocks, { chunk_type });
				VectorRemove(possible_blocks, { chunk_type });
				break;
			case STR2INT("stsz"):
				GENERATE_VAR(stsz_block, ::g->stsz_block.generate());
				VectorRemove(preferred_blocks, { "stsc", "stsz", "stz2" });
				VectorRemove(possible_blocks, { "stsc", "stsz", "stz2" });
				break;
			case STR2INT("stz2"):
				GENERATE_VAR(stz2_block, ::g->stz2_block.generate());
				VectorRemove(preferred_blocks, { "stsc", "stsz", "stz2" });
				VectorRemove(possible_blocks, { "stsc", "stsz", "stz2" });
				break;
			case STR2INT("stts"):
				GENERATE_VAR(stts_block, ::g->stts_block.generate());
				VectorRemove(preferred_blocks, { chunk_type });
				VectorRemove(possible_blocks, { chunk_type });
				break;
			case STR2INT("ctts"):
				GENERATE_VAR(ctts_block, ::g->ctts_block.generate());
				break;
			case STR2INT("stss"):
				GENERATE_VAR(stss_block, ::g->stss_block.generate());
				VectorRemove(possible_blocks, { chunk_type });
				break;
			case STR2INT("stsh"):
				GENERATE_VAR(stsh_block, ::g->stsh_block.generate());
				break;
			case STR2INT("stdb"):
				GENERATE_VAR(stdb_block, ::g->stdb_block.generate());
				VectorRemove(possible_blocks, { chunk_type });
				break;
			case STR2INT("sdtp"):
				GENERATE_VAR(sdtp_block, ::g->sdtp_block.generate());
				VectorRemove(possible_blocks, { chunk_type });
				break;
			case STR2INT("sbgp"):
				GENERATE_VAR(sbgp_block, ::g->sbgp_block.generate());
				VectorRemove(possible_blocks, { chunk_type });
				break;
			case STR2INT("sgpd"):
				GENERATE_VAR(sgpd_block, ::g->sgpd_block.generate());
				VectorRemove(possible_blocks, { chunk_type });
				break;
			case STR2INT("subs"):
				GENERATE_VAR(subs_block, ::g->subs_block.generate());
				VectorRemove(possible_blocks, { chunk_type });
				break;
			default:
				GENERATE_VAR(unknown_block, ::g->unknown_block.generate());
				break;
			};
			if (((startOffset + size()) == (uint64)FTell())) {
				break;
			};
		};
		break;
	case STR2INT("stsd"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(entry_count, ::g->entry_count.generate({ 1 }));
		;
		chunk_type.resize(4);
		if (::g->isVideo) {
			preferred_blocks = { "avc1" };
			possible_blocks = { "avc1" };
		} else {
			preferred_blocks = { "mp4a" };
			possible_blocks = { "mp4a" };
		};
		for (i = 0; (i < entry_count()); i++) {
				ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks);
			GENERATE_VAR(mixed_box, ::g->mixed_box.generate());
		;
		};
		break;
	case STR2INT("avc1"):
		tmp = 0;
		for ( ; (tmp < 6); tmp++) {
			GENERATE(reserved, ::g->reserved___.generate({ 0 }));
		};
		GENERATE_VAR(data_reference_index, ::g->data_reference_index.generate({ 1 }));
		for (tmp = 0; (tmp < 16); tmp++) {
			GENERATE(reserved, ::g->reserved___.generate({ 0 }));
		};
		GENERATE(width, ::g->width_.generate());
		GENERATE(height, ::g->height_.generate());
		GENERATE_VAR(horizresolution, ::g->horizresolution.generate({ 0x00480000 }));
		GENERATE_VAR(vertresolution, ::g->vertresolution.generate({ 0x00480000 }));
		GENERATE(reserved, ::g->reserved_.generate({ 0 }));
		GENERATE_VAR(frame_count, ::g->frame_count.generate({ 1 }));
		GENERATE_VAR(compressorname, ::g->compressorname.generate(32));
		GENERATE_VAR(depth, ::g->depth.generate({ 0x0018 }));
		GENERATE(pre_defined, ::g->pre_defined_.generate({ 0x0018 }));
		blocks = { "avcC" };
		while (ReadBytes(chunk_type, (FTell() + 4), 4, blocks, blocks)) {
			if ((chunk_type == "avcC")) {
				GENERATE_VAR(avcC_box, ::g->avcC_box.generate());
				VectorRemove(blocks, { chunk_type });
			} else {
				GENERATE_VAR(unknown_box, ::g->unknown_box.generate());
			};
			if (((startOffset + size()) == (uint64)FTell())) {
				break;
			};
		};
		break;
	case STR2INT("avcC"):
		GENERATE_VAR(configurationVersion, ::g->configurationVersion.generate({ 1 }));
		GENERATE_VAR(AVCProfileIndication, ::g->AVCProfileIndication.generate());
		GENERATE_VAR(profile_compatibility, ::g->profile_compatibility.generate());
		GENERATE_VAR(AVCLevelIndication, ::g->AVCLevelIndication.generate());
		GENERATE_VAR(reserved_lengthSizeMinusOne, ::g->reserved_lengthSizeMinusOne.generate({ 0xFC, 0xFD, 0xFE, 0xFF }));
		GENERATE_VAR(reserved_numOfSequenceParameterSets, ::g->reserved_numOfSequenceParameterSets.generate({ 0xE1 }));
		tmp_masked = 1;
		;
		for (j = 0; (j < tmp_masked); j++) {
				GENERATE_VAR(sequenceParameterSetLength, ::g->sequenceParameterSetLength.generate({ 0x18 }));
			GENERATE_VAR(sequenceParameterSetNALUnit, ::g->sequenceParameterSetNALUnit.generate(sequenceParameterSetLength()));
		;
		};
		GENERATE_VAR(numOfPictureParameterSets, ::g->numOfPictureParameterSets.generate({ 1 }));
		for (j = 0; (j < numOfPictureParameterSets()); j++) {
				GENERATE_VAR(pictureParameterSetLength, ::g->pictureParameterSetLength.generate({ 0x06 }));
			GENERATE_VAR(pictureParameterSetNALUnit, ::g->pictureParameterSetNALUnit.generate(pictureParameterSetLength()));
		;
		};
		break;
	case STR2INT("mp4a"):
		GENERATE_VAR(reserved_a, ::g->reserved_a.generate({ 0 }));
		GENERATE_VAR(reserved_b, ::g->reserved_b.generate({ 0 }));
		GENERATE_VAR(data_reference_index, ::g->data_reference_index.generate({ 1 }));
		GENERATE_VAR(reserved_c, ::g->reserved_c.generate({ 0 }));
		GENERATE_VAR(channelcount, ::g->channelcount.generate({ 2 }));
		GENERATE_VAR(samplesize, ::g->samplesize.generate({ 16 }));
		GENERATE(pre_defined, ::g->pre_defined_.generate({ 0 }));
		GENERATE_VAR(reserved_d, ::g->reserved_d.generate({ 0 }));
		GENERATE_VAR(samplerate_tmp, ::g->samplerate_tmp.generate());
		FSeek((FTell() - 2));
		;
		tmp = (samplerate_tmp() * 65536);
		GENERATE_VAR(samplerate, ::g->samplerate.generate({ tmp }));
		chunk_type.resize(4);
		preferred_blocks = { "esds" };
		ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks);
		GENERATE_VAR(esds_box, ::g->esds_box.generate());
		break;
	case STR2INT("esds"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(sectionID_3, ::g->sectionID_3.generate({ 58753152 }));
		GENERATE_VAR(data_a, ::g->data_a.generate({ 620756992 }));
		GENERATE_VAR(sectionID_4, ::g->sectionID_4.generate({ 75530368 }));
		GENERATE_VAR(data_b, ::g->data_b.generate({ 390075648 }));
		GENERATE_VAR(reserved_d, ::g->reserved_d.generate({ 0 }));
		GENERATE_VAR(reserved_e, ::g->reserved_e.generate({ 0 }));
		GENERATE_VAR(sectionID_5, ::g->sectionID_5.generate({ 92307584 }));
		GENERATE_VAR(data_e, ::g->data_e.generate({ 85069910 }));
		GENERATE_VAR(data_f, ::g->data_f.generate({ 58624 }));
		GENERATE_VAR(sectionID_6, ::g->sectionID_6.generate({ 109084800 }));
		GENERATE_VAR(data_f, ::g->data_f.generate({ 258 }));
		break;
	case STR2INT("vide"):
		break;
	case STR2INT("hint"):
		break;
	case STR2INT("stts"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(entry_count, ::g->entry_count.generate({ 1 }));
		GENERATE(entry, ::g->entry.generate(entry_count()));
		break;
	case STR2INT("elst"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE(flags, ::g->flags.generate(3));
		GENERATE_VAR(num_entries, ::g->num_entries.generate());
		GENERATE_VAR(entries, ::g->entries.generate(num_entries()));
		break;
	case STR2INT("cprt"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE(language, ::g->language_.generate(3));
		GENERATE_VAR(notice, ::g->notice.generate());
		break;
	case STR2INT("iinf"):
		GENERATE_VAR(entry_count_16_tmp, ::g->entry_count_16_tmp.generate());
		FSeek((FTell() - 2));
		tmp_16 = (entry_count_16_tmp() % 16);
		GENERATE_VAR(entry_count_16, ::g->entry_count_16.generate({ tmp_16 }));
		;
		for (i = 0; (i < entry_count_16()); i++) {
				GENERATE_VAR(item_ID, ::g->item_ID.generate({ (uint16)i }));
			GENERATE_VAR(item_protection_index, ::g->item_protection_index.generate());
			GENERATE_VAR(item_name, ::g->item_name.generate());
			GENERATE_VAR(content_type, ::g->content_type.generate());
			GENERATE_VAR(content_encoding, ::g->content_encoding.generate());
		;
		};
		break;
	case STR2INT("dinf"):
		chunk_type.resize(4);
		prefered_blocks = { "url " };
		ReadBytes(chunk_type, (FTell() + 4), 4, prefered_blocks, prefered_blocks);
		switch (STR2INT(chunk_type)) {
		case STR2INT("url "):
			GENERATE_VAR(url_box, ::g->url_box.generate());
			break;
		case STR2INT("dref"):
			GENERATE_VAR(dref_box, ::g->dref_box.generate());
			break;
		case STR2INT("urn "):
			GENERATE_VAR(urn_box, ::g->urn_box.generate());
			break;
		default:
			GENERATE_VAR(unknown_block, ::g->unknown_block.generate());
			break;
		};
		break;
	case STR2INT("url "):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(location, ::g->location.generate());
		break;
	case STR2INT("urn "):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(name, ::g->name.generate());
		GENERATE_VAR(location, ::g->location.generate());
		break;
	case STR2INT("smhd"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE(flags, ::g->flags.generate(3));
		GENERATE_VAR(balance, ::g->balance.generate());
		GENERATE(reserved, ::g->reserved____.generate());
		break;
	case STR2INT("vmhd"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE(flags, ::g->flags__.generate());
		GENERATE_VAR(graphics_mode, qtgfxmode_generate({ 0 }));
		GENERATE_VAR(opcolor, ::g->opcolor.generate());
		break;
	case STR2INT("stsc"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(entry_count, ::g->entry_count.generate({ 1 }));
		;
		sampleCount = 0;
		currentIndex = 1;
		for (i = 1; (i <= entry_count()); i++) {
				GENERATE_VAR(first_chunk, ::g->first_chunk.generate({ currentIndex }));
			currentIndex = (currentIndex + 1);
			GENERATE_VAR(samples_per_chunk, ::g->samples_per_chunk.generate());
			sampleCount = (sampleCount + samples_per_chunk());
			GENERATE_VAR(sample_description_index, ::g->sample_description_index.generate({ i }));
		;
		};
		::g->sharedSamplecountVar = sampleCount;
		break;
	case STR2INT("co64"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(entry_count, ::g->entry_count.generate());
		GENERATE(chunk_offset, ::g->chunk_offset.generate(entry_count()));
		break;
	case STR2INT("stco"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(entry_count, ::g->entry_count.generate({ 1 }));
		;
		for (i = 0; (i < entry_count()); i++) {
				GENERATE(chunk_offset, ::g->chunk_offset_.generate({ ::g->mdatPosition }));
		;
		};
		break;
	case STR2INT("stsz"):
		GENERATE_VAR(version, ::g->version.generate({ 0 }));
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(sample_size, ::g->sample_size.generate());
		GENERATE_VAR(sample_count, ::g->sample_count.generate({ ::g->sharedSamplecountVar }));
		if ((sample_size() < 1)) {
			for (i = 0; (i < sample_count()); i++) {
					GENERATE_VAR(entry_size, ::g->entry_size.generate({ 16 }));
			;
			};
		};
		break;
	case STR2INT("frma"):
		GENERATE_VAR(codingName, ::g->codingName.generate());
		break;
	case STR2INT("tenc"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(reserved1, ::g->reserved1.generate());
		if ((version() < 1)) {
			GENERATE(reserved2, ::g->reserved2_.generate());
		} else {
			GENERATE_VAR(default_crypt_skip_byte_block, ::g->default_crypt_skip_byte_block.generate());
		};
		GENERATE_VAR(default_is_protected, ::g->default_is_protected.generate());
		GENERATE_VAR(default_per_sample_IV_size, ::g->default_per_sample_IV_size.generate());
		GENERATE_VAR(default_KID, ::g->default_KID.generate(16));
		if ((0 == default_per_sample_IV_size())) {
			GENERATE_VAR(default_constant_IV_size, ::g->default_constant_IV_size.generate());
			GENERATE_VAR(default_constant_IV, ::g->default_constant_IV.generate(default_constant_IV_size()));
		};
		break;
	case STR2INT("schm"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(scheme_type, ::g->scheme_type.generate());
		GENERATE_VAR(scheme_version, ::g->scheme_version.generate());
		break;
	case STR2INT("pssh"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(systemID, ::g->systemID.generate(16));
		if ((version() > 0)) {
			GENERATE_VAR(KID_count, ::g->KID_count.generate());
			GENERATE_VAR(KID, ::g->KID.generate(KID_count()));
		};
		GENERATE_VAR(DataSize, ::g->DataSize.generate());
		GENERATE_VAR(Data, ::g->Data.generate(DataSize()));
		break;
	case STR2INT("senc"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(sample_count, ::g->sample_count.generate());
		GENERATE(entry, ::g->entry__.generate(sample_count()));
		break;
	case STR2INT("saio"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		if (((flag()[2] & 1) != 0)) {
			GENERATE_VAR(aux_info_type, ::g->aux_info_type.generate());
			GENERATE_VAR(aud_info_type_parameter, ::g->aud_info_type_parameter.generate());
		};
		GENERATE_VAR(entry_count, ::g->entry_count.generate());
		if ((version() == 0)) {
			GENERATE(offset, ::g->offset.generate(entry_count()));
		} else {
			GENERATE(offset, ::g->offset_.generate(entry_count()));
		};
		break;
	case STR2INT("saiz"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		if (((flag()[2] & 1) != 0)) {
			GENERATE_VAR(aux_info_type, ::g->aux_info_type.generate());
			GENERATE_VAR(aux_info_type_parameter, ::g->aux_info_type_parameter.generate());
		};
		GENERATE_VAR(default_sample_info_size, ::g->default_sample_info_size.generate());
		GENERATE_VAR(sample_count, ::g->sample_count.generate());
		if ((default_sample_info_size() == 0)) {
			GENERATE(entry, ::g->entry_.generate(sample_count()));
		};
		break;
	case STR2INT("trun"):
		;
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(sample_count, ::g->sample_count.generate());
		if (((flag()[2] & 1) != 0)) {
			GENERATE_VAR(data_offset, ::g->data_offset.generate());
		};
		if (((flag()[2] & 4) != 0)) {
			GENERATE_VAR(first_sample_flags, ::g->first_sample_flags.generate());
		};
		for (i = 0; (i < sample_count()); i++) {
				GENERATE(entry, ::g->entry___.generate());
		;
		};
		break;
	case STR2INT("tfhd"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(trackID, ::g->trackID.generate());
		if ((0 != (flag()[2] & 1))) {
			GENERATE_VAR(base_data_offset, ::g->base_data_offset.generate());
		};
		if ((0 != (flag()[2] & 2))) {
			GENERATE_VAR(sample_description_index, ::g->sample_description_index.generate());
		};
		if ((0 != (flag()[2] & 8))) {
			GENERATE_VAR(default_sample_duration, ::g->default_sample_duration.generate());
		};
		if ((0 != (flag()[2] & 0x10))) {
			GENERATE_VAR(default_sample_size, ::g->default_sample_size.generate());
		};
		if ((0 != (flag()[2] & 0x20))) {
			GENERATE_VAR(default_sample_flags, ::g->default_sample_flags.generate());
		};
		break;
	case STR2INT("mfhd"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(sequence_number, ::g->sequence_number.generate());
		break;
	case STR2INT("sidx"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(referenceID, ::g->referenceID.generate());
		GENERATE_VAR(timescale, ::g->timescale.generate());
		if ((version() < 1)) {
			GENERATE(earliest_presentation_time, ::g->earliest_presentation_time.generate());
			GENERATE(first_offset, ::g->first_offset.generate());
		} else {
			GENERATE(earliest_presentation_time, ::g->earliest_presentation_time_.generate());
			GENERATE(first_offset, ::g->first_offset_.generate());
		};
		GENERATE(reserved, ::g->reserved____.generate());
		GENERATE_VAR(reference_count, ::g->reference_count.generate());
		GENERATE_VAR(references, ::g->references.generate(reference_count()));
		break;
	case STR2INT("trex"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(trackID, ::g->trackID.generate());
		GENERATE_VAR(default_sample_description_index, ::g->default_sample_description_index.generate());
		GENERATE_VAR(default_sample_duration, ::g->default_sample_duration.generate());
		GENERATE_VAR(default_sample_size, ::g->default_sample_size.generate());
		GENERATE_VAR(default_sample_flags, ::g->default_sample_flags.generate());
		break;
	case STR2INT("mehd"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		if ((version() == 0)) {
			GENERATE(fragment_duration, ::g->fragment_duration.generate());
		} else {
			GENERATE(fragment_duration, ::g->fragment_duration_.generate());
		};
		break;
	case STR2INT("enca"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		GENERATE_VAR(entry_count, ::g->entry_count.generate());
		GENERATE_VAR(data, ::g->data.generate(0x14));
		break;
	case STR2INT("stss"):
		GENERATE_VAR(version, ::g->version.generate());
		GENERATE_VAR(flag, ::g->flag.generate(3));
		before_entry_count = FTell();
		GENERATE_VAR(entry_count, ::g->entry_count.generate());
		ChangeArrayLength();
		GENERATE_VAR(sample_number, ::g->sample_number.generate(entry_count()));
		EndChangeArrayLength();
		after = FTell();
		correct_count = (((after - before_entry_count) - 4) / 4);
		if ((entry_count() != correct_count)) {
			FSeek(before_entry_count);
			evil = SetEvilBit(false);
			GENERATE_VAR(entry_count, ::g->entry_count.generate({ correct_count }));
			SetEvilBit(evil);
			FSeek(after);
		};
		break;
	default:
		ChangeArrayLength();
		GENERATE_VAR(unknown, ::g->unknown.generate(contentsize));
		EndChangeArrayLength();
		break;
	};
	if ((size() && (FTell() != endOffset))) {
		parsedSize = (FTell() - startOffset);
		Warning("Parsed %u bytes and expected %u bytes in chunk %s", parsedSize, size(), std::string(type().value()).c_str());
		FSeek(endOffset);
	};
	writePosition = FTell();
	FSeek(startOffset);
	newSize = (writePosition - startOffset);
	evil = SetEvilBit(false);
	GENERATE_VAR(size, ::g->size.generate({ newSize }));
	SetEvilBit(evil);
	FSeek(writePosition);

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


mp4file* mp4file::generate() {
	if (generated == 1) {
		mp4file* new_instance = new mp4file(instances);
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

	chunk_type.resize(4);
	preferred_blocks = { "ftyp" };
	possible_blocks = { "ftyp" };
	while (ReadBytes(chunk_type, (FTell() + 4), 4, preferred_blocks, possible_blocks)) {
		switch (STR2INT(chunk_type)) {
		case STR2INT("ftyp"):
			GENERATE_VAR(ftyp_block, ::g->ftyp_block.generate());
			preferred_blocks = { "mdat", "moov" };
			possible_blocks = { "mdat", "moov", "free" };
			break;
		case STR2INT("mdat"):
			GENERATE_VAR(mdat_block, ::g->mdat_block.generate());
			VectorRemove(preferred_blocks, { "mdat" });
			VectorRemove(possible_blocks, { "mdat" });
			break;
		case STR2INT("moov"):
			GENERATE_VAR(moov_block, ::g->moov_block.generate());
			VectorRemove(preferred_blocks, { "moov" });
			VectorRemove(possible_blocks, { "moov" });
			break;
		case STR2INT("free"):
			GENERATE_VAR(free_block, ::g->free_block.generate());
			break;
		default:
			GENERATE_VAR(unknown_block, ::g->unknown_block.generate());
			break;
		};
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}



void generate_file() {
	::g = new globals_class();

	BigEndian();
	::g->sharedSamplecountVar = 0;
	::g->mdatPosition = 0;
	::g->isVideo = false;
	GENERATE(file, ::g->file.generate());

	file_acc.finish();
	delete_globals();
}

void delete_globals() { delete ::g; }

