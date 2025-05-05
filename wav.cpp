#include <cstdlib>
#include <cstdio>
#include <string>
#include <vector>
#include <unordered_map>
#include "bt.h"
typedef LONG SMPLLOOPS_Cue_ID;
typedef LONG SMPLLOOPS_Play_Count;
typedef LONG SMPLLOOPS_Start;
typedef LONG SMPLLOOPS_End;
typedef LONG SMPLLOOPS_Fraction;
typedef LONG SMPL_SL;
typedef LONG SMPL_SD;
typedef LONG SMPL_SMPTE_Offset;
typedef LONG SMPL_MIDI_Pitch_Fraction;
typedef LONG SMPL_MIDI_Unity_Note;
typedef LONG SMPL_Product;
typedef LONG SMPL_Sample_Period;
typedef LONG SMPL_SMPTE;
typedef LONG SMPL_Manufacturer;
typedef LONG SMPLLOOPS_Type;

enum e_Format_Tags : ushort {
	PCM = (ushort) 0x0001,
};
std::vector<ushort> e_Format_Tags_values = { PCM };

typedef enum e_Format_Tags E_FORMAT_TAGS;
std::vector<ushort> E_FORMAT_TAGS_values = { PCM };


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



class long_class {
	int small;
	std::vector<LONG> known_values;
	LONG value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(LONG);
	LONG operator () () { return value; }
	long_class(int small, std::vector<LONG> known_values = {}) : small(small), known_values(known_values) {}

	LONG generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(LONG), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(LONG), 0, known_values);
		}
		return value;
	}

	LONG generate(std::vector<LONG> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(LONG), 0, possible_values);
		return value;
	}
};



class WAVRIFFHEADER {
	std::vector<WAVRIFFHEADER*>& instances;

	std::string groupID_var;
	LONG hsize_var;
	std::string riffType_var;

public:
	bool groupID_exists = false;
	bool hsize_exists = false;
	bool riffType_exists = false;

	std::string& groupID() {
		assert_cond(groupID_exists, "struct field groupID does not exist");
		return groupID_var;
	}
	LONG& hsize() {
		assert_cond(hsize_exists, "struct field hsize does not exist");
		return hsize_var;
	}
	std::string& riffType() {
		assert_cond(riffType_exists, "struct field riffType does not exist");
		return riffType_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	WAVRIFFHEADER& operator () () { return *instances.back(); }
	WAVRIFFHEADER& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	WAVRIFFHEADER(std::vector<WAVRIFFHEADER*>& instances) : instances(instances) { instances.push_back(this); }
	~WAVRIFFHEADER() {
		if (generated == 2)
			return;
		while (instances.size()) {
			WAVRIFFHEADER* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	WAVRIFFHEADER* generate();
};

int WAVRIFFHEADER::_parent_id = 0;
int WAVRIFFHEADER::_index_start = 0;


E_FORMAT_TAGS E_FORMAT_TAGS_generate() {
	return (E_FORMAT_TAGS) file_acc.file_integer(sizeof(ushort), 0, E_FORMAT_TAGS_values);
}

E_FORMAT_TAGS E_FORMAT_TAGS_generate(std::vector<ushort> known_values) {
	return (E_FORMAT_TAGS) file_acc.file_integer(sizeof(ushort), 0, known_values);
}


class unsigned_short_class {
	int small;
	std::vector<unsigned short> known_values;
	unsigned short value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(unsigned short);
	unsigned short operator () () { return value; }
	unsigned_short_class(int small, std::vector<unsigned short> known_values = {}) : small(small), known_values(known_values) {}

	unsigned short generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(unsigned short), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(unsigned short), 0, known_values);
		}
		return value;
	}

	unsigned short generate(std::vector<unsigned short> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(unsigned short), 0, possible_values);
		return value;
	}
};



class unsigned_long_class {
	int small;
	std::vector<ULONG> known_values;
	ULONG value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(ULONG);
	ULONG operator () () { return value; }
	unsigned_long_class(int small, std::vector<ULONG> known_values = {}) : small(small), known_values(known_values) {}

	ULONG generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(ULONG), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(ULONG), 0, known_values);
		}
		return value;
	}

	ULONG generate(std::vector<ULONG> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(ULONG), 0, possible_values);
		return value;
	}
};



class uchar_class {
	int small;
	std::vector<uchar> known_values;
	uchar value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(uchar);
	uchar operator () () { return value; }
	uchar_class(int small, std::vector<uchar> known_values = {}) : small(small), known_values(known_values) {}

	uchar generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(uchar), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(uchar), 0, known_values);
		}
		return value;
	}

	uchar generate(std::vector<uchar> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(uchar), 0, possible_values);
		return value;
	}
};



class uchar_array_class {
	uchar_class& element;
	std::vector<std::string> known_values;
	std::unordered_map<int, std::vector<uchar>> element_known_values;
	std::string value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::string& operator () () { return value; }
	uchar operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	uchar_array_class(uchar_class& element, std::unordered_map<int, std::vector<uchar>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}
	uchar_array_class(uchar_class& element, std::vector<std::string> known_values)
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
				value.push_back(file_acc.file_integer(sizeof(uchar), 0, known->second));
				_sizeof += sizeof(uchar);
			}
		}
		return value;
	}
};



class FORMATCHUNK {
	std::vector<FORMATCHUNK*>& instances;

	std::string chunkID_var;
	LONG chunkSize_var;
	ushort wFormatTag_var;
	unsigned short wChannels_var;
	ULONG dwSamplesPerSec_var;
	ULONG dwAvgBytesPerSec_var;
	unsigned short dummy_var;
	unsigned short wBitsPerSample_var;
	unsigned short wBlockAlign_var;
	unsigned short wcbsize_var;
	unsigned short wSamplesPerBlock_var;
	std::string unknown_var;
	uchar padding_var;

public:
	bool chunkID_exists = false;
	bool chunkSize_exists = false;
	bool wFormatTag_exists = false;
	bool wChannels_exists = false;
	bool dwSamplesPerSec_exists = false;
	bool dwAvgBytesPerSec_exists = false;
	bool dummy_exists = false;
	bool wBitsPerSample_exists = false;
	bool wBlockAlign_exists = false;
	bool wcbsize_exists = false;
	bool wSamplesPerBlock_exists = false;
	bool unknown_exists = false;
	bool padding_exists = false;

	std::string& chunkID() {
		assert_cond(chunkID_exists, "struct field chunkID does not exist");
		return chunkID_var;
	}
	LONG& chunkSize() {
		assert_cond(chunkSize_exists, "struct field chunkSize does not exist");
		return chunkSize_var;
	}
	ushort& wFormatTag() {
		assert_cond(wFormatTag_exists, "struct field wFormatTag does not exist");
		return wFormatTag_var;
	}
	unsigned short& wChannels() {
		assert_cond(wChannels_exists, "struct field wChannels does not exist");
		return wChannels_var;
	}
	ULONG& dwSamplesPerSec() {
		assert_cond(dwSamplesPerSec_exists, "struct field dwSamplesPerSec does not exist");
		return dwSamplesPerSec_var;
	}
	ULONG& dwAvgBytesPerSec() {
		assert_cond(dwAvgBytesPerSec_exists, "struct field dwAvgBytesPerSec does not exist");
		return dwAvgBytesPerSec_var;
	}
	unsigned short& dummy() {
		assert_cond(dummy_exists, "struct field dummy does not exist");
		return dummy_var;
	}
	unsigned short& wBitsPerSample() {
		assert_cond(wBitsPerSample_exists, "struct field wBitsPerSample does not exist");
		return wBitsPerSample_var;
	}
	unsigned short& wBlockAlign() {
		assert_cond(wBlockAlign_exists, "struct field wBlockAlign does not exist");
		return wBlockAlign_var;
	}
	unsigned short& wcbsize() {
		assert_cond(wcbsize_exists, "struct field wcbsize does not exist");
		return wcbsize_var;
	}
	unsigned short& wSamplesPerBlock() {
		assert_cond(wSamplesPerBlock_exists, "struct field wSamplesPerBlock does not exist");
		return wSamplesPerBlock_var;
	}
	std::string& unknown() {
		assert_cond(unknown_exists, "struct field unknown does not exist");
		return unknown_var;
	}
	uchar& padding() {
		assert_cond(padding_exists, "struct field padding does not exist");
		return padding_var;
	}

	/* locals */
	int pos;
	unsigned short dummy_pos;
	unsigned short bps_pos;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	FORMATCHUNK& operator () () { return *instances.back(); }
	FORMATCHUNK& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	FORMATCHUNK(std::vector<FORMATCHUNK*>& instances) : instances(instances) { instances.push_back(this); }
	~FORMATCHUNK() {
		if (generated == 2)
			return;
		while (instances.size()) {
			FORMATCHUNK* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	FORMATCHUNK* generate();
};

int FORMATCHUNK::_parent_id = 0;
int FORMATCHUNK::_index_start = 0;



class unsigned_char_class {
	int small;
	std::vector<unsigned char> known_values;
	unsigned char value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(unsigned char);
	unsigned char operator () () { return value; }
	unsigned_char_class(int small, std::vector<unsigned char> known_values = {}) : small(small), known_values(known_values) {}

	unsigned char generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(unsigned char), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(unsigned char), 0, known_values);
		}
		return value;
	}

	unsigned char generate(std::vector<unsigned char> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(unsigned char), 0, possible_values);
		return value;
	}
};



class unsigned_char_array_class {
	unsigned_char_class& element;
	std::vector<std::string> known_values;
	std::unordered_map<int, std::vector<unsigned char>> element_known_values;
	std::string value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::string& operator () () { return value; }
	unsigned char operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	unsigned_char_array_class(unsigned_char_class& element, std::unordered_map<int, std::vector<unsigned char>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}
	unsigned_char_array_class(unsigned_char_class& element, std::vector<std::string> known_values)
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
				value.push_back(file_acc.file_integer(sizeof(unsigned char), 0, known->second));
				_sizeof += sizeof(unsigned char);
			}
		}
		return value;
	}
};



class short_class {
	int small;
	std::vector<short> known_values;
	short value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(short);
	short operator () () { return value; }
	short_class(int small, std::vector<short> known_values = {}) : small(small), known_values(known_values) {}

	short generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(short), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(short), 0, known_values);
		}
		return value;
	}

	short generate(std::vector<short> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(short), 0, possible_values);
		return value;
	}
};



class short_array_class {
	short_class& element;
	std::unordered_map<int, std::vector<short>> element_known_values;
	std::vector<short> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<short>& operator () () { return value; }
	short operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	short_array_class(short_class& element, std::unordered_map<int, std::vector<short>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}

	std::vector<short> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			auto known = element_known_values.find(i);
			if (known == element_known_values.end()) {
				value.push_back(element.generate());
				_sizeof += element._sizeof;
			} else {
				value.push_back(file_acc.file_integer(sizeof(short), 0, known->second));
				_sizeof += sizeof(short);
			}
		}
		return value;
	}
};



class int_class {
	int small;
	std::vector<int> known_values;
	int value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(int);
	int operator () () { return value; }
	int_class(int small, std::vector<int> known_values = {}) : small(small), known_values(known_values) {}

	int generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(int), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(int), 0, known_values);
		}
		return value;
	}

	int generate(std::vector<int> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(int), 0, possible_values);
		return value;
	}
};



class int_array_class {
	int_class& element;
	std::unordered_map<int, std::vector<int>> element_known_values;
	std::vector<int> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<int>& operator () () { return value; }
	int operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	int_array_class(int_class& element, std::unordered_map<int, std::vector<int>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}

	std::vector<int> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			auto known = element_known_values.find(i);
			if (known == element_known_values.end()) {
				value.push_back(element.generate());
				_sizeof += element._sizeof;
			} else {
				value.push_back(file_acc.file_integer(sizeof(int), 0, known->second));
				_sizeof += sizeof(int);
			}
		}
		return value;
	}
};



class SAMPLES {
	std::vector<SAMPLES*>& instances;


public:


	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	SAMPLES& operator () () { return *instances.back(); }
	SAMPLES& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	SAMPLES(std::vector<SAMPLES*>& instances) : instances(instances) { instances.push_back(this); }
	~SAMPLES() {
		if (generated == 2)
			return;
		while (instances.size()) {
			SAMPLES* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	SAMPLES* generate();
};

int SAMPLES::_parent_id = 0;
int SAMPLES::_index_start = 0;



class SAMPLES_array_class {
	SAMPLES& element;
	std::vector<SAMPLES*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<SAMPLES*>& operator () () { return value; }
	SAMPLES operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	SAMPLES_array_class(SAMPLES& element) : element(element) {}

	std::vector<SAMPLES*> generate(unsigned size) {
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



class DATACHUNK {
	std::vector<DATACHUNK*>& instances;

	std::string chunkID_var;
	LONG chunkSize_temp_var;
	LONG chunkSize_var;
	std::string waveformData_var;
	uchar padding_var;

public:
	bool chunkID_exists = false;
	bool chunkSize_temp_exists = false;
	bool chunkSize_exists = false;
	bool waveformData_exists = false;
	bool padding_exists = false;

	std::string& chunkID() {
		assert_cond(chunkID_exists, "struct field chunkID does not exist");
		return chunkID_var;
	}
	LONG& chunkSize_temp() {
		assert_cond(chunkSize_temp_exists, "struct field chunkSize_temp does not exist");
		return chunkSize_temp_var;
	}
	LONG& chunkSize() {
		assert_cond(chunkSize_exists, "struct field chunkSize does not exist");
		return chunkSize_var;
	}
	std::string& waveformData() {
		assert_cond(waveformData_exists, "struct field waveformData does not exist");
		return waveformData_var;
	}
	uchar& padding() {
		assert_cond(padding_exists, "struct field padding does not exist");
		return padding_var;
	}

	/* locals */
	int size_pos;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	DATACHUNK& operator () () { return *instances.back(); }
	DATACHUNK& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	DATACHUNK(std::vector<DATACHUNK*>& instances) : instances(instances) { instances.push_back(this); }
	~DATACHUNK() {
		if (generated == 2)
			return;
		while (instances.size()) {
			DATACHUNK* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	DATACHUNK* generate();
};

int DATACHUNK::_parent_id = 0;
int DATACHUNK::_index_start = 0;



class FACTCHUNK {
	std::vector<FACTCHUNK*>& instances;

	std::string chunkID_var;
	LONG chunkSize_var;
	ULONG uncompressedSize_var;

public:
	bool chunkID_exists = false;
	bool chunkSize_exists = false;
	bool uncompressedSize_exists = false;

	std::string& chunkID() {
		assert_cond(chunkID_exists, "struct field chunkID does not exist");
		return chunkID_var;
	}
	LONG& chunkSize() {
		assert_cond(chunkSize_exists, "struct field chunkSize does not exist");
		return chunkSize_var;
	}
	ULONG& uncompressedSize() {
		assert_cond(uncompressedSize_exists, "struct field uncompressedSize does not exist");
		return uncompressedSize_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	FACTCHUNK& operator () () { return *instances.back(); }
	FACTCHUNK& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	FACTCHUNK(std::vector<FACTCHUNK*>& instances) : instances(instances) { instances.push_back(this); }
	~FACTCHUNK() {
		if (generated == 2)
			return;
		while (instances.size()) {
			FACTCHUNK* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	FACTCHUNK* generate();
};

int FACTCHUNK::_parent_id = 0;
int FACTCHUNK::_index_start = 0;



class CUEPOINT {
	std::vector<CUEPOINT*>& instances;

	LONG dwIdentifier_var;
	LONG dwPosition_var;
	std::string fccChunk_var;
	LONG dwChunkStart_var;
	LONG dwBlockStart_var;
	LONG dwSampleOffset_var;

public:
	bool dwIdentifier_exists = false;
	bool dwPosition_exists = false;
	bool fccChunk_exists = false;
	bool dwChunkStart_exists = false;
	bool dwBlockStart_exists = false;
	bool dwSampleOffset_exists = false;

	LONG& dwIdentifier() {
		assert_cond(dwIdentifier_exists, "struct field dwIdentifier does not exist");
		return dwIdentifier_var;
	}
	LONG& dwPosition() {
		assert_cond(dwPosition_exists, "struct field dwPosition does not exist");
		return dwPosition_var;
	}
	std::string& fccChunk() {
		assert_cond(fccChunk_exists, "struct field fccChunk does not exist");
		return fccChunk_var;
	}
	LONG& dwChunkStart() {
		assert_cond(dwChunkStart_exists, "struct field dwChunkStart does not exist");
		return dwChunkStart_var;
	}
	LONG& dwBlockStart() {
		assert_cond(dwBlockStart_exists, "struct field dwBlockStart does not exist");
		return dwBlockStart_var;
	}
	LONG& dwSampleOffset() {
		assert_cond(dwSampleOffset_exists, "struct field dwSampleOffset does not exist");
		return dwSampleOffset_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	CUEPOINT& operator () () { return *instances.back(); }
	CUEPOINT& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	CUEPOINT(std::vector<CUEPOINT*>& instances) : instances(instances) { instances.push_back(this); }
	~CUEPOINT() {
		if (generated == 2)
			return;
		while (instances.size()) {
			CUEPOINT* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	CUEPOINT* generate();
};

int CUEPOINT::_parent_id = 0;
int CUEPOINT::_index_start = 0;



class CUEPOINT_array_class {
	CUEPOINT& element;
	std::vector<CUEPOINT*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<CUEPOINT*>& operator () () { return value; }
	CUEPOINT operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	CUEPOINT_array_class(CUEPOINT& element) : element(element) {}

	std::vector<CUEPOINT*> generate(unsigned size) {
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



class CUECHUNK {
	std::vector<CUECHUNK*>& instances;

	std::string chunkID_var;
	LONG chunkSize_var;
	LONG dwCuePoints_var;
	std::vector<CUEPOINT*> points_var;
	std::string unknown_var;

public:
	bool chunkID_exists = false;
	bool chunkSize_exists = false;
	bool dwCuePoints_exists = false;
	bool points_exists = false;
	bool unknown_exists = false;

	std::string& chunkID() {
		assert_cond(chunkID_exists, "struct field chunkID does not exist");
		return chunkID_var;
	}
	LONG& chunkSize() {
		assert_cond(chunkSize_exists, "struct field chunkSize does not exist");
		return chunkSize_var;
	}
	LONG& dwCuePoints() {
		assert_cond(dwCuePoints_exists, "struct field dwCuePoints does not exist");
		return dwCuePoints_var;
	}
	std::vector<CUEPOINT*>& points() {
		assert_cond(points_exists, "struct field points does not exist");
		return points_var;
	}
	std::string& unknown() {
		assert_cond(unknown_exists, "struct field unknown does not exist");
		return unknown_var;
	}

	/* locals */
	int size_pos;
	int pos;
	LONG end;
	int evil;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	CUECHUNK& operator () () { return *instances.back(); }
	CUECHUNK& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	CUECHUNK(std::vector<CUECHUNK*>& instances) : instances(instances) { instances.push_back(this); }
	~CUECHUNK() {
		if (generated == 2)
			return;
		while (instances.size()) {
			CUECHUNK* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	CUECHUNK* generate();
};

int CUECHUNK::_parent_id = 0;
int CUECHUNK::_index_start = 0;



class SMPL_Manufacturer_class {
	int small;
	std::vector<SMPL_Manufacturer> known_values;
	SMPL_Manufacturer value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPL_Manufacturer);
	SMPL_Manufacturer operator () () { return value; }
	SMPL_Manufacturer_class(int small, std::vector<SMPL_Manufacturer> known_values = {}) : small(small), known_values(known_values) {}

	SMPL_Manufacturer generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPL_Manufacturer), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPL_Manufacturer), 0, known_values);
		}
		return value;
	}

	SMPL_Manufacturer generate(std::vector<SMPL_Manufacturer> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPL_Manufacturer), 0, possible_values);
		return value;
	}
};



class SMPL_Product_class {
	int small;
	std::vector<SMPL_Product> known_values;
	SMPL_Product value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPL_Product);
	SMPL_Product operator () () { return value; }
	SMPL_Product_class(int small, std::vector<SMPL_Product> known_values = {}) : small(small), known_values(known_values) {}

	SMPL_Product generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPL_Product), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPL_Product), 0, known_values);
		}
		return value;
	}

	SMPL_Product generate(std::vector<SMPL_Product> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPL_Product), 0, possible_values);
		return value;
	}
};



class SMPL_Sample_Period_class {
	int small;
	std::vector<SMPL_Sample_Period> known_values;
	SMPL_Sample_Period value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPL_Sample_Period);
	SMPL_Sample_Period operator () () { return value; }
	SMPL_Sample_Period_class(int small, std::vector<SMPL_Sample_Period> known_values = {}) : small(small), known_values(known_values) {}

	SMPL_Sample_Period generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPL_Sample_Period), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPL_Sample_Period), 0, known_values);
		}
		return value;
	}

	SMPL_Sample_Period generate(std::vector<SMPL_Sample_Period> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPL_Sample_Period), 0, possible_values);
		return value;
	}
};



class SMPL_MIDI_Unity_Note_class {
	int small;
	std::vector<SMPL_MIDI_Unity_Note> known_values;
	SMPL_MIDI_Unity_Note value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPL_MIDI_Unity_Note);
	SMPL_MIDI_Unity_Note operator () () { return value; }
	SMPL_MIDI_Unity_Note_class(int small, std::vector<SMPL_MIDI_Unity_Note> known_values = {}) : small(small), known_values(known_values) {}

	SMPL_MIDI_Unity_Note generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPL_MIDI_Unity_Note), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPL_MIDI_Unity_Note), 0, known_values);
		}
		return value;
	}

	SMPL_MIDI_Unity_Note generate(std::vector<SMPL_MIDI_Unity_Note> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPL_MIDI_Unity_Note), 0, possible_values);
		return value;
	}
};



class SMPL_MIDI_Pitch_Fraction_class {
	int small;
	std::vector<SMPL_MIDI_Pitch_Fraction> known_values;
	SMPL_MIDI_Pitch_Fraction value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPL_MIDI_Pitch_Fraction);
	SMPL_MIDI_Pitch_Fraction operator () () { return value; }
	SMPL_MIDI_Pitch_Fraction_class(int small, std::vector<SMPL_MIDI_Pitch_Fraction> known_values = {}) : small(small), known_values(known_values) {}

	SMPL_MIDI_Pitch_Fraction generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPL_MIDI_Pitch_Fraction), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPL_MIDI_Pitch_Fraction), 0, known_values);
		}
		return value;
	}

	SMPL_MIDI_Pitch_Fraction generate(std::vector<SMPL_MIDI_Pitch_Fraction> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPL_MIDI_Pitch_Fraction), 0, possible_values);
		return value;
	}
};



class SMPL_SMPTE_class {
	int small;
	std::vector<SMPL_SMPTE> known_values;
	SMPL_SMPTE value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPL_SMPTE);
	SMPL_SMPTE operator () () { return value; }
	SMPL_SMPTE_class(int small, std::vector<SMPL_SMPTE> known_values = {}) : small(small), known_values(known_values) {}

	SMPL_SMPTE generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPL_SMPTE), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPL_SMPTE), 0, known_values);
		}
		return value;
	}

	SMPL_SMPTE generate(std::vector<SMPL_SMPTE> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPL_SMPTE), 0, possible_values);
		return value;
	}
};



class SMPL_SMPTE_Offset_class {
	int small;
	std::vector<SMPL_SMPTE_Offset> known_values;
	SMPL_SMPTE_Offset value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPL_SMPTE_Offset);
	SMPL_SMPTE_Offset operator () () { return value; }
	SMPL_SMPTE_Offset_class(int small, std::vector<SMPL_SMPTE_Offset> known_values = {}) : small(small), known_values(known_values) {}

	SMPL_SMPTE_Offset generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPL_SMPTE_Offset), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPL_SMPTE_Offset), 0, known_values);
		}
		return value;
	}

	SMPL_SMPTE_Offset generate(std::vector<SMPL_SMPTE_Offset> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPL_SMPTE_Offset), 0, possible_values);
		return value;
	}
};



class SMPL_SL_class {
	int small;
	std::vector<SMPL_SL> known_values;
	SMPL_SL value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPL_SL);
	SMPL_SL operator () () { return value; }
	SMPL_SL_class(int small, std::vector<SMPL_SL> known_values = {}) : small(small), known_values(known_values) {}

	SMPL_SL generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPL_SL), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPL_SL), 0, known_values);
		}
		return value;
	}

	SMPL_SL generate(std::vector<SMPL_SL> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPL_SL), 0, possible_values);
		return value;
	}
};



class SMPL_SD_class {
	int small;
	std::vector<SMPL_SD> known_values;
	SMPL_SD value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPL_SD);
	SMPL_SD operator () () { return value; }
	SMPL_SD_class(int small, std::vector<SMPL_SD> known_values = {}) : small(small), known_values(known_values) {}

	SMPL_SD generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPL_SD), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPL_SD), 0, known_values);
		}
		return value;
	}

	SMPL_SD generate(std::vector<SMPL_SD> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPL_SD), 0, possible_values);
		return value;
	}
};



class SMPLLOOPS_Cue_ID_class {
	int small;
	std::vector<SMPLLOOPS_Cue_ID> known_values;
	SMPLLOOPS_Cue_ID value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPLLOOPS_Cue_ID);
	SMPLLOOPS_Cue_ID operator () () { return value; }
	SMPLLOOPS_Cue_ID_class(int small, std::vector<SMPLLOOPS_Cue_ID> known_values = {}) : small(small), known_values(known_values) {}

	SMPLLOOPS_Cue_ID generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Cue_ID), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Cue_ID), 0, known_values);
		}
		return value;
	}

	SMPLLOOPS_Cue_ID generate(std::vector<SMPLLOOPS_Cue_ID> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPLLOOPS_Cue_ID), 0, possible_values);
		return value;
	}
};



class SMPLLOOPS_Type_class {
	int small;
	std::vector<SMPLLOOPS_Type> known_values;
	SMPLLOOPS_Type value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPLLOOPS_Type);
	SMPLLOOPS_Type operator () () { return value; }
	SMPLLOOPS_Type_class(int small, std::vector<SMPLLOOPS_Type> known_values = {}) : small(small), known_values(known_values) {}

	SMPLLOOPS_Type generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Type), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Type), 0, known_values);
		}
		return value;
	}

	SMPLLOOPS_Type generate(std::vector<SMPLLOOPS_Type> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPLLOOPS_Type), 0, possible_values);
		return value;
	}
};



class SMPLLOOPS_Start_class {
	int small;
	std::vector<SMPLLOOPS_Start> known_values;
	SMPLLOOPS_Start value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPLLOOPS_Start);
	SMPLLOOPS_Start operator () () { return value; }
	SMPLLOOPS_Start_class(int small, std::vector<SMPLLOOPS_Start> known_values = {}) : small(small), known_values(known_values) {}

	SMPLLOOPS_Start generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Start), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Start), 0, known_values);
		}
		return value;
	}

	SMPLLOOPS_Start generate(std::vector<SMPLLOOPS_Start> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPLLOOPS_Start), 0, possible_values);
		return value;
	}
};



class SMPLLOOPS_End_class {
	int small;
	std::vector<SMPLLOOPS_End> known_values;
	SMPLLOOPS_End value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPLLOOPS_End);
	SMPLLOOPS_End operator () () { return value; }
	SMPLLOOPS_End_class(int small, std::vector<SMPLLOOPS_End> known_values = {}) : small(small), known_values(known_values) {}

	SMPLLOOPS_End generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_End), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_End), 0, known_values);
		}
		return value;
	}

	SMPLLOOPS_End generate(std::vector<SMPLLOOPS_End> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPLLOOPS_End), 0, possible_values);
		return value;
	}
};



class SMPLLOOPS_Fraction_class {
	int small;
	std::vector<SMPLLOOPS_Fraction> known_values;
	SMPLLOOPS_Fraction value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPLLOOPS_Fraction);
	SMPLLOOPS_Fraction operator () () { return value; }
	SMPLLOOPS_Fraction_class(int small, std::vector<SMPLLOOPS_Fraction> known_values = {}) : small(small), known_values(known_values) {}

	SMPLLOOPS_Fraction generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Fraction), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Fraction), 0, known_values);
		}
		return value;
	}

	SMPLLOOPS_Fraction generate(std::vector<SMPLLOOPS_Fraction> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPLLOOPS_Fraction), 0, possible_values);
		return value;
	}
};



class SMPLLOOPS_Play_Count_class {
	int small;
	std::vector<SMPLLOOPS_Play_Count> known_values;
	SMPLLOOPS_Play_Count value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(SMPLLOOPS_Play_Count);
	SMPLLOOPS_Play_Count operator () () { return value; }
	SMPLLOOPS_Play_Count_class(int small, std::vector<SMPLLOOPS_Play_Count> known_values = {}) : small(small), known_values(known_values) {}

	SMPLLOOPS_Play_Count generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Play_Count), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(SMPLLOOPS_Play_Count), 0, known_values);
		}
		return value;
	}

	SMPLLOOPS_Play_Count generate(std::vector<SMPLLOOPS_Play_Count> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(SMPLLOOPS_Play_Count), 0, possible_values);
		return value;
	}
};



class SMPLLOOPS {
	std::vector<SMPLLOOPS*>& instances;

	SMPLLOOPS_Cue_ID Cue_Point_var;
	SMPLLOOPS_Type Type_var;
	SMPLLOOPS_Start Start_var;
	SMPLLOOPS_End End_var;
	SMPLLOOPS_Fraction Fraction_var;
	SMPLLOOPS_Play_Count Play_Count_var;

public:
	bool Cue_Point_exists = false;
	bool Type_exists = false;
	bool Start_exists = false;
	bool End_exists = false;
	bool Fraction_exists = false;
	bool Play_Count_exists = false;

	SMPLLOOPS_Cue_ID& Cue_Point() {
		assert_cond(Cue_Point_exists, "struct field Cue_Point does not exist");
		return Cue_Point_var;
	}
	SMPLLOOPS_Type& Type() {
		assert_cond(Type_exists, "struct field Type does not exist");
		return Type_var;
	}
	SMPLLOOPS_Start& Start() {
		assert_cond(Start_exists, "struct field Start does not exist");
		return Start_var;
	}
	SMPLLOOPS_End& End() {
		assert_cond(End_exists, "struct field End does not exist");
		return End_var;
	}
	SMPLLOOPS_Fraction& Fraction() {
		assert_cond(Fraction_exists, "struct field Fraction does not exist");
		return Fraction_var;
	}
	SMPLLOOPS_Play_Count& Play_Count() {
		assert_cond(Play_Count_exists, "struct field Play_Count does not exist");
		return Play_Count_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	SMPLLOOPS& operator () () { return *instances.back(); }
	SMPLLOOPS& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	SMPLLOOPS(std::vector<SMPLLOOPS*>& instances) : instances(instances) { instances.push_back(this); }
	~SMPLLOOPS() {
		if (generated == 2)
			return;
		while (instances.size()) {
			SMPLLOOPS* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	SMPLLOOPS* generate();
};

int SMPLLOOPS::_parent_id = 0;
int SMPLLOOPS::_index_start = 0;



class SMPLLOOPS_array_class {
	SMPLLOOPS& element;
	std::vector<SMPLLOOPS*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<SMPLLOOPS*>& operator () () { return value; }
	SMPLLOOPS operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	SMPLLOOPS_array_class(SMPLLOOPS& element) : element(element) {}

	std::vector<SMPLLOOPS*> generate(unsigned size) {
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



class SMPLCHUNK {
	std::vector<SMPLCHUNK*>& instances;

	std::string chunkID_var;
	LONG chunkSize_var;
	SMPL_Manufacturer Manufacturer_var;
	SMPL_Product Product_var;
	SMPL_Sample_Period Sample_Period_var;
	SMPL_MIDI_Unity_Note MIDI_Unity_Note_var;
	SMPL_MIDI_Pitch_Fraction MIDI_Pitch_Fraction_var;
	SMPL_SMPTE SMPTE_var;
	SMPL_SMPTE_Offset SMPTE_Offset_var;
	SMPL_SL Num_Sample_Loops_var;
	SMPL_SD Sampler_Data_var;
	std::vector<SMPLLOOPS*> loops_var;
	uchar padding_var;

public:
	bool chunkID_exists = false;
	bool chunkSize_exists = false;
	bool Manufacturer_exists = false;
	bool Product_exists = false;
	bool Sample_Period_exists = false;
	bool MIDI_Unity_Note_exists = false;
	bool MIDI_Pitch_Fraction_exists = false;
	bool SMPTE_exists = false;
	bool SMPTE_Offset_exists = false;
	bool Num_Sample_Loops_exists = false;
	bool Sampler_Data_exists = false;
	bool loops_exists = false;
	bool padding_exists = false;

	std::string& chunkID() {
		assert_cond(chunkID_exists, "struct field chunkID does not exist");
		return chunkID_var;
	}
	LONG& chunkSize() {
		assert_cond(chunkSize_exists, "struct field chunkSize does not exist");
		return chunkSize_var;
	}
	SMPL_Manufacturer& Manufacturer() {
		assert_cond(Manufacturer_exists, "struct field Manufacturer does not exist");
		return Manufacturer_var;
	}
	SMPL_Product& Product() {
		assert_cond(Product_exists, "struct field Product does not exist");
		return Product_var;
	}
	SMPL_Sample_Period& Sample_Period() {
		assert_cond(Sample_Period_exists, "struct field Sample_Period does not exist");
		return Sample_Period_var;
	}
	SMPL_MIDI_Unity_Note& MIDI_Unity_Note() {
		assert_cond(MIDI_Unity_Note_exists, "struct field MIDI_Unity_Note does not exist");
		return MIDI_Unity_Note_var;
	}
	SMPL_MIDI_Pitch_Fraction& MIDI_Pitch_Fraction() {
		assert_cond(MIDI_Pitch_Fraction_exists, "struct field MIDI_Pitch_Fraction does not exist");
		return MIDI_Pitch_Fraction_var;
	}
	SMPL_SMPTE& SMPTE() {
		assert_cond(SMPTE_exists, "struct field SMPTE does not exist");
		return SMPTE_var;
	}
	SMPL_SMPTE_Offset& SMPTE_Offset() {
		assert_cond(SMPTE_Offset_exists, "struct field SMPTE_Offset does not exist");
		return SMPTE_Offset_var;
	}
	SMPL_SL& Num_Sample_Loops() {
		assert_cond(Num_Sample_Loops_exists, "struct field Num_Sample_Loops does not exist");
		return Num_Sample_Loops_var;
	}
	SMPL_SD& Sampler_Data() {
		assert_cond(Sampler_Data_exists, "struct field Sampler_Data does not exist");
		return Sampler_Data_var;
	}
	std::vector<SMPLLOOPS*>& loops() {
		assert_cond(loops_exists, "struct field loops does not exist");
		return loops_var;
	}
	uchar& padding() {
		assert_cond(padding_exists, "struct field padding does not exist");
		return padding_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	SMPLCHUNK& operator () () { return *instances.back(); }
	SMPLCHUNK& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	SMPLCHUNK(std::vector<SMPLCHUNK*>& instances) : instances(instances) { instances.push_back(this); }
	~SMPLCHUNK() {
		if (generated == 2)
			return;
		while (instances.size()) {
			SMPLCHUNK* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	SMPLCHUNK* generate();
};

int SMPLCHUNK::_parent_id = 0;
int SMPLCHUNK::_index_start = 0;



class LISTSUBCHUNK {
	std::vector<LISTSUBCHUNK*>& instances;

	std::string chunkID_var;
	LONG chunkSize_var;
	std::string listData_var;
	uchar padding_var;

public:
	bool chunkID_exists = false;
	bool chunkSize_exists = false;
	bool listData_exists = false;
	bool padding_exists = false;

	std::string& chunkID() {
		assert_cond(chunkID_exists, "struct field chunkID does not exist");
		return chunkID_var;
	}
	LONG& chunkSize() {
		assert_cond(chunkSize_exists, "struct field chunkSize does not exist");
		return chunkSize_var;
	}
	std::string& listData() {
		assert_cond(listData_exists, "struct field listData does not exist");
		return listData_var;
	}
	uchar& padding() {
		assert_cond(padding_exists, "struct field padding does not exist");
		return padding_var;
	}

	/* locals */
	int size_pos;
	LONG end;
	LONG real_size;
	int evil;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	LISTSUBCHUNK& operator () () { return *instances.back(); }
	LISTSUBCHUNK& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	LISTSUBCHUNK(std::vector<LISTSUBCHUNK*>& instances) : instances(instances) { instances.push_back(this); }
	~LISTSUBCHUNK() {
		if (generated == 2)
			return;
		while (instances.size()) {
			LISTSUBCHUNK* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	LISTSUBCHUNK* generate();
};

int LISTSUBCHUNK::_parent_id = 0;
int LISTSUBCHUNK::_index_start = 0;



class LISTCHUNK {
	std::vector<LISTCHUNK*>& instances;

	std::string chunkID_var;
	LONG chunkSize_var;
	std::string chunkType_var;
	LISTSUBCHUNK* subchunk_var;
	std::string unknown_var;
	uchar padding_var;

public:
	bool chunkID_exists = false;
	bool chunkSize_exists = false;
	bool chunkType_exists = false;
	bool subchunk_exists = false;
	bool unknown_exists = false;
	bool padding_exists = false;

	std::string& chunkID() {
		assert_cond(chunkID_exists, "struct field chunkID does not exist");
		return chunkID_var;
	}
	LONG& chunkSize() {
		assert_cond(chunkSize_exists, "struct field chunkSize does not exist");
		return chunkSize_var;
	}
	std::string& chunkType() {
		assert_cond(chunkType_exists, "struct field chunkType does not exist");
		return chunkType_var;
	}
	LISTSUBCHUNK& subchunk() {
		assert_cond(subchunk_exists, "struct field subchunk does not exist");
		return *subchunk_var;
	}
	std::string& unknown() {
		assert_cond(unknown_exists, "struct field unknown does not exist");
		return unknown_var;
	}
	uchar& padding() {
		assert_cond(padding_exists, "struct field padding does not exist");
		return padding_var;
	}

	/* locals */
	quad pos;
	std::string list_tag;
	uint size;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	LISTCHUNK& operator () () { return *instances.back(); }
	LISTCHUNK& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	LISTCHUNK(std::vector<LISTCHUNK*>& instances) : instances(instances) { instances.push_back(this); }
	~LISTCHUNK() {
		if (generated == 2)
			return;
		while (instances.size()) {
			LISTCHUNK* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	LISTCHUNK* generate();
};

int LISTCHUNK::_parent_id = 0;
int LISTCHUNK::_index_start = 0;



class UNKNOWNCHUNK {
	std::vector<UNKNOWNCHUNK*>& instances;

	std::string chunkID_var;
	LONG chunkSize_var;
	std::string unknownData_var;
	uchar padding_var;

public:
	bool chunkID_exists = false;
	bool chunkSize_exists = false;
	bool unknownData_exists = false;
	bool padding_exists = false;

	std::string& chunkID() {
		assert_cond(chunkID_exists, "struct field chunkID does not exist");
		return chunkID_var;
	}
	LONG& chunkSize() {
		assert_cond(chunkSize_exists, "struct field chunkSize does not exist");
		return chunkSize_var;
	}
	std::string& unknownData() {
		assert_cond(unknownData_exists, "struct field unknownData does not exist");
		return unknownData_var;
	}
	uchar& padding() {
		assert_cond(padding_exists, "struct field padding does not exist");
		return padding_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	UNKNOWNCHUNK& operator () () { return *instances.back(); }
	UNKNOWNCHUNK& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	UNKNOWNCHUNK(std::vector<UNKNOWNCHUNK*>& instances) : instances(instances) { instances.push_back(this); }
	~UNKNOWNCHUNK() {
		if (generated == 2)
			return;
		while (instances.size()) {
			UNKNOWNCHUNK* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	UNKNOWNCHUNK* generate();
};

int UNKNOWNCHUNK::_parent_id = 0;
int UNKNOWNCHUNK::_index_start = 0;

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
std::vector<std::string> ReadBytesInitValues = { "fmt ", "data", "fact", "cue ", "smpl", "LIST", "id3 " };


std::vector<WAVRIFFHEADER*> WAVRIFFHEADER_header_instances;
std::vector<FORMATCHUNK*> FORMATCHUNK_format_instances;
std::vector<SAMPLES*> SAMPLES_samples____element_instances;
std::vector<DATACHUNK*> DATACHUNK_data_instances;
std::vector<FACTCHUNK*> FACTCHUNK_fact_instances;
std::vector<CUEPOINT*> CUEPOINT_points_element_instances;
std::vector<CUECHUNK*> CUECHUNK_cue_instances;
std::vector<SMPLLOOPS*> SMPLLOOPS_loops_element_instances;
std::vector<SMPLCHUNK*> SMPLCHUNK_smpl_instances;
std::vector<LISTSUBCHUNK*> LISTSUBCHUNK_subchunk_instances;
std::vector<LISTCHUNK*> LISTCHUNK_list_instances;
std::vector<UNKNOWNCHUNK*> UNKNOWNCHUNK_unknown__instances;


std::unordered_map<std::string, std::string> variable_types = { { "groupID", "char_array_class" }, { "hsize", "long_class" }, { "riffType", "char_array_class" }, { "header", "WAVRIFFHEADER" }, { "chunkID", "char_array_class" }, { "chunkSize", "long_class" }, { "wFormatTag", "E_FORMAT_TAGS" }, { "wChannels", "unsigned_short_class" }, { "dwSamplesPerSec", "unsigned_long_class" }, { "dwAvgBytesPerSec", "unsigned_long_class" }, { "dummy", "unsigned_short_class" }, { "wBitsPerSample", "unsigned_short_class" }, { "wBlockAlign", "unsigned_short_class" }, { "wcbsize", "unsigned_short_class" }, { "wSamplesPerBlock", "unsigned_short_class" }, { "unknown", "uchar_array_class" }, { "padding", "uchar_class" }, { "format", "FORMATCHUNK" }, { "chunkSize_temp", "long_class" }, { "waveformData", "unsigned_char_array_class" }, { "samples", "uchar_array_class" }, { "samples_", "short_array_class" }, { "samples__", "int_array_class" }, { "channels", "uchar_array_class" }, { "channels_", "short_array_class" }, { "channels__", "int_array_class" }, { "samples___", "SAMPLES_array_class" }, { "data", "DATACHUNK" }, { "uncompressedSize", "unsigned_long_class" }, { "fact", "FACTCHUNK" }, { "dwCuePoints", "long_class" }, { "dwIdentifier", "long_class" }, { "dwPosition", "long_class" }, { "fccChunk", "char_array_class" }, { "dwChunkStart", "long_class" }, { "dwBlockStart", "long_class" }, { "dwSampleOffset", "long_class" }, { "points", "CUEPOINT_array_class" }, { "cue", "CUECHUNK" }, { "Manufacturer", "SMPL_Manufacturer_class" }, { "Product", "SMPL_Product_class" }, { "Sample_Period", "SMPL_Sample_Period_class" }, { "MIDI_Unity_Note", "SMPL_MIDI_Unity_Note_class" }, { "MIDI_Pitch_Fraction", "SMPL_MIDI_Pitch_Fraction_class" }, { "SMPTE", "SMPL_SMPTE_class" }, { "SMPTE_Offset", "SMPL_SMPTE_Offset_class" }, { "Num_Sample_Loops", "SMPL_SL_class" }, { "Sampler_Data", "SMPL_SD_class" }, { "Cue_Point", "SMPLLOOPS_Cue_ID_class" }, { "Type", "SMPLLOOPS_Type_class" }, { "Start", "SMPLLOOPS_Start_class" }, { "End", "SMPLLOOPS_End_class" }, { "Fraction", "SMPLLOOPS_Fraction_class" }, { "Play_Count", "SMPLLOOPS_Play_Count_class" }, { "loops", "SMPLLOOPS_array_class" }, { "smpl", "SMPLCHUNK" }, { "chunkType", "char_array_class" }, { "listData", "char_array_class" }, { "subchunk", "LISTSUBCHUNK" }, { "list", "LISTCHUNK" }, { "unknownData", "uchar_array_class" }, { "unknown_", "UNKNOWNCHUNK" } };

std::vector<std::vector<int>> integer_ranges = { { 1, 16 }, { 1, 256 }, { 1, 16 }, { 1, 16 } };

class globals_class {
public:
	int _struct_id = 0;
	int _struct_id_counter = 0;
	/*local*/ int haveValidFormat;
	/*local*/ int data_size;
	char_class groupID_element;
	char_array_class groupID;
	long_class hsize;
	char_class riffType_element;
	char_array_class riffType;
	WAVRIFFHEADER header;
	/*local*/ std::string chunk_tag;
	/*local*/ int compressed_wav;
	/*local*/ std::vector<std::string> tag_values_possible;
	/*local*/ std::vector<std::string> tag_values_preferred;
	char_class chunkID_element;
	char_array_class chunkID;
	long_class chunkSize;
	unsigned_short_class wChannels;
	unsigned_long_class dwSamplesPerSec;
	unsigned_long_class dwAvgBytesPerSec;
	unsigned_short_class dummy;
	unsigned_short_class wBitsPerSample;
	unsigned_short_class wBlockAlign;
	unsigned_short_class wcbsize;
	unsigned_short_class wSamplesPerBlock;
	uchar_class unknown_element;
	uchar_array_class unknown;
	uchar_class padding;
	FORMATCHUNK format;
	long_class chunkSize_temp;
	unsigned_char_class waveformData_element;
	unsigned_char_array_class waveformData;
	uchar_class samples_element;
	uchar_array_class samples;
	short_class samples__element;
	short_array_class samples_;
	int_class samples___element;
	int_array_class samples__;
	uchar_class channels_element;
	uchar_array_class channels;
	short_class channels__element;
	short_array_class channels_;
	int_class channels___element;
	int_array_class channels__;
	SAMPLES samples____element;
	SAMPLES_array_class samples___;
	DATACHUNK data;
	unsigned_long_class uncompressedSize;
	FACTCHUNK fact;
	long_class dwCuePoints;
	long_class dwIdentifier;
	long_class dwPosition;
	char_class fccChunk_element;
	char_array_class fccChunk;
	long_class dwChunkStart;
	long_class dwBlockStart;
	long_class dwSampleOffset;
	CUEPOINT points_element;
	CUEPOINT_array_class points;
	CUECHUNK cue;
	SMPL_Manufacturer_class Manufacturer;
	SMPL_Product_class Product;
	SMPL_Sample_Period_class Sample_Period;
	SMPL_MIDI_Unity_Note_class MIDI_Unity_Note;
	SMPL_MIDI_Pitch_Fraction_class MIDI_Pitch_Fraction;
	SMPL_SMPTE_class SMPTE;
	SMPL_SMPTE_Offset_class SMPTE_Offset;
	SMPL_SL_class Num_Sample_Loops;
	SMPL_SD_class Sampler_Data;
	SMPLLOOPS_Cue_ID_class Cue_Point;
	SMPLLOOPS_Type_class Type;
	SMPLLOOPS_Start_class Start;
	SMPLLOOPS_End_class End;
	SMPLLOOPS_Fraction_class Fraction;
	SMPLLOOPS_Play_Count_class Play_Count;
	SMPLLOOPS loops_element;
	SMPLLOOPS_array_class loops;
	SMPLCHUNK smpl;
	char_class chunkType_element;
	char_array_class chunkType;
	char_class listData_element;
	char_array_class listData;
	LISTSUBCHUNK subchunk;
	LISTCHUNK list;
	uchar_class unknownData_element;
	uchar_array_class unknownData;
	UNKNOWNCHUNK unknown_;
	/*local*/ int file_size;


	globals_class() :
		groupID_element(false),
		groupID(groupID_element, { "RIFF" }),
		hsize(1),
		riffType_element(false),
		riffType(riffType_element, { "WAVE" }),
		header(WAVRIFFHEADER_header_instances),
		chunkID_element(false),
		chunkID(chunkID_element),
		chunkSize(1),
		wChannels(3),
		dwSamplesPerSec(1),
		dwAvgBytesPerSec(1),
		dummy(1),
		wBitsPerSample(1, { 8, 16, 32, 8, 16, 32, 8, 16, 32 }),
		wBlockAlign(1, { 0 }),
		wcbsize(1),
		wSamplesPerBlock(1),
		unknown_element(false),
		unknown(unknown_element),
		padding(1),
		format(FORMATCHUNK_format_instances),
		chunkSize_temp(4),
		waveformData_element(false),
		waveformData(waveformData_element),
		samples_element(false),
		samples(samples_element),
		samples__element(false),
		samples_(samples__element),
		samples___element(false),
		samples__(samples___element),
		channels_element(false),
		channels(channels_element),
		channels__element(false),
		channels_(channels__element),
		channels___element(false),
		channels__(channels___element),
		samples____element(SAMPLES_samples____element_instances),
		samples___(samples____element),
		data(DATACHUNK_data_instances),
		uncompressedSize(1),
		fact(FACTCHUNK_fact_instances),
		dwCuePoints(5),
		dwIdentifier(1),
		dwPosition(1),
		fccChunk_element(false),
		fccChunk(fccChunk_element),
		dwChunkStart(1),
		dwBlockStart(1),
		dwSampleOffset(1),
		points_element(CUEPOINT_points_element_instances),
		points(points_element),
		cue(CUECHUNK_cue_instances),
		Manufacturer(1),
		Product(1),
		Sample_Period(1),
		MIDI_Unity_Note(1),
		MIDI_Pitch_Fraction(1),
		SMPTE(1),
		SMPTE_Offset(1),
		Num_Sample_Loops(1),
		Sampler_Data(1),
		Cue_Point(1),
		Type(1),
		Start(1),
		End(1),
		Fraction(1),
		Play_Count(1),
		loops_element(SMPLLOOPS_loops_element_instances),
		loops(loops_element),
		smpl(SMPLCHUNK_smpl_instances),
		chunkType_element(false),
		chunkType(chunkType_element),
		listData_element(false),
		listData(listData_element),
		subchunk(LISTSUBCHUNK_subchunk_instances),
		list(LISTCHUNK_list_instances),
		unknownData_element(false),
		unknownData(unknownData_element),
		unknown_(UNKNOWNCHUNK_unknown__instances)
	{}
};

globals_class* g;


WAVRIFFHEADER* WAVRIFFHEADER::generate() {
	if (generated == 1) {
		WAVRIFFHEADER* new_instance = new WAVRIFFHEADER(instances);
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

	GENERATE_VAR(groupID, ::g->groupID.generate(4));
	GENERATE_VAR(hsize, ::g->hsize.generate());
	GENERATE_VAR(riffType, ::g->riffType.generate(4));

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


FORMATCHUNK* FORMATCHUNK::generate() {
	if (generated == 1) {
		FORMATCHUNK* new_instance = new FORMATCHUNK(instances);
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

	GENERATE_VAR(chunkID, ::g->chunkID.generate(4));
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate({ 16 }));
	pos = FTell();
	GENERATE_VAR(wFormatTag, E_FORMAT_TAGS_generate());
	GENERATE_VAR(wChannels, ::g->wChannels.generate());
	::g->data_size += wChannels();
	GENERATE_VAR(dwSamplesPerSec, ::g->dwSamplesPerSec.generate());
	GENERATE_VAR(dwAvgBytesPerSec, ::g->dwAvgBytesPerSec.generate());
	dummy_pos = FTell();
	GENERATE_VAR(dummy, ::g->dummy.generate());
	GENERATE_VAR(wBitsPerSample, ::g->wBitsPerSample.generate({ 8, 16, 32 }));
	::g->data_size = (::g->data_size * (wBitsPerSample() / 8));
	bps_pos = FTell();
	FSeek(dummy_pos);
	GENERATE_VAR(wBlockAlign, ::g->wBlockAlign.generate({ (unsigned short)((wBitsPerSample() / 8) * wChannels()) }));
	FSeek(bps_pos);
	if ((wFormatTag() == 17)) {
		GENERATE_VAR(wcbsize, ::g->wcbsize.generate());
		GENERATE_VAR(wSamplesPerBlock, ::g->wSamplesPerBlock.generate());
	};
	::g->haveValidFormat = true;
	if ((chunkSize() > (FTell() - pos))) {
		GENERATE_VAR(unknown, ::g->unknown.generate((chunkSize() - (FTell() - pos))));
	};
	if ((chunkSize() & 1)) {
		GENERATE_VAR(padding, ::g->padding.generate());
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


SAMPLES* SAMPLES::generate() {
	if (generated == 1) {
		SAMPLES* new_instance = new SAMPLES(instances);
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

	if ((::g->format().wBitsPerSample() == 8)) {
		GENERATE(channels, ::g->channels.generate(::g->format().wChannels()));
	} else {
	if ((::g->format().wBitsPerSample() == 16)) {
		GENERATE(channels, ::g->channels_.generate(::g->format().wChannels()));
	} else {
	if ((::g->format().wBitsPerSample() == 32)) {
		GENERATE(channels, ::g->channels__.generate(::g->format().wChannels()));
	};
	};
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


DATACHUNK* DATACHUNK::generate() {
	if (generated == 1) {
		DATACHUNK* new_instance = new DATACHUNK(instances);
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

	GENERATE_VAR(chunkID, ::g->chunkID.generate(4));
	size_pos = FTell();
	GENERATE_VAR(chunkSize_temp, ::g->chunkSize_temp.generate());
	FSeek(size_pos);
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate({ (chunkSize_temp() * ::g->data_size) }));
	if (!::g->haveValidFormat) {
		Warning("File contains no valid WAVE format chunk.");
		exit_template(-1);
	};
	if ((((((::g->format().wBitsPerSample() != 8) && (::g->format().wBitsPerSample() != 16)) && (::g->format().wBitsPerSample() != 32)) || (::g->format().wBlockAlign() == 0)) || ((chunkSize() % (int)::g->format().wBlockAlign()) != 0))) {
		GENERATE_VAR(waveformData, ::g->waveformData.generate(chunkSize()));
	} else {
	if (((::g->format().wChannels() == 1) && (::g->format().wBitsPerSample() == 8))) {
		GENERATE(samples, ::g->samples.generate(chunkSize()));
	} else {
	if (((::g->format().wChannels() == 1) && (::g->format().wBitsPerSample() == 16))) {
		GENERATE(samples, ::g->samples_.generate((chunkSize() / 2)));
	} else {
	if (((::g->format().wChannels() == 1) && (::g->format().wBitsPerSample() == 32))) {
		GENERATE(samples, ::g->samples__.generate((chunkSize() / 4)));
	} else {
		GENERATE(samples, ::g->samples___.generate((chunkSize() / (int)::g->format().wBlockAlign())));
	};
	};
	};
	};
	if (((chunkSize() & 1) && !FEof(0.0))) {
		GENERATE_VAR(padding, ::g->padding.generate());
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


FACTCHUNK* FACTCHUNK::generate() {
	if (generated == 1) {
		FACTCHUNK* new_instance = new FACTCHUNK(instances);
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

	GENERATE_VAR(chunkID, ::g->chunkID.generate(4));
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate({ 12 }));
	GENERATE_VAR(uncompressedSize, ::g->uncompressedSize.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


CUEPOINT* CUEPOINT::generate() {
	if (generated == 1) {
		CUEPOINT* new_instance = new CUEPOINT(instances);
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

	GENERATE_VAR(dwIdentifier, ::g->dwIdentifier.generate());
	GENERATE_VAR(dwPosition, ::g->dwPosition.generate());
	GENERATE_VAR(fccChunk, ::g->fccChunk.generate(4));
	GENERATE_VAR(dwChunkStart, ::g->dwChunkStart.generate());
	GENERATE_VAR(dwBlockStart, ::g->dwBlockStart.generate());
	GENERATE_VAR(dwSampleOffset, ::g->dwSampleOffset.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


CUECHUNK* CUECHUNK::generate() {
	if (generated == 1) {
		CUECHUNK* new_instance = new CUECHUNK(instances);
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

	GENERATE_VAR(chunkID, ::g->chunkID.generate(4));
	size_pos = FTell();
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate());
	pos = FTell();
	GENERATE_VAR(dwCuePoints, ::g->dwCuePoints.generate());
	GENERATE_VAR(points, ::g->points.generate(dwCuePoints()));
	end = FTell();
	FSeek(size_pos);
	evil = SetEvilBit(false);
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate({ (end - pos) }));
	SetEvilBit(evil);
	FSeek(end);
	if ((chunkSize() > (FTell() - pos))) {
		GENERATE_VAR(unknown, ::g->unknown.generate((chunkSize() - (FTell() - pos))));
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


SMPLLOOPS* SMPLLOOPS::generate() {
	if (generated == 1) {
		SMPLLOOPS* new_instance = new SMPLLOOPS(instances);
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

	GENERATE_VAR(Cue_Point, ::g->Cue_Point.generate());
	GENERATE_VAR(Type, ::g->Type.generate());
	GENERATE_VAR(Start, ::g->Start.generate());
	GENERATE_VAR(End, ::g->End.generate());
	GENERATE_VAR(Fraction, ::g->Fraction.generate());
	GENERATE_VAR(Play_Count, ::g->Play_Count.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


SMPLCHUNK* SMPLCHUNK::generate() {
	if (generated == 1) {
		SMPLCHUNK* new_instance = new SMPLCHUNK(instances);
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

	GENERATE_VAR(chunkID, ::g->chunkID.generate(4));
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate());
	GENERATE_VAR(Manufacturer, ::g->Manufacturer.generate());
	GENERATE_VAR(Product, ::g->Product.generate());
	GENERATE_VAR(Sample_Period, ::g->Sample_Period.generate());
	GENERATE_VAR(MIDI_Unity_Note, ::g->MIDI_Unity_Note.generate());
	GENERATE_VAR(MIDI_Pitch_Fraction, ::g->MIDI_Pitch_Fraction.generate());
	GENERATE_VAR(SMPTE, ::g->SMPTE.generate());
	GENERATE_VAR(SMPTE_Offset, ::g->SMPTE_Offset.generate());
	GENERATE_VAR(Num_Sample_Loops, ::g->Num_Sample_Loops.generate());
	GENERATE_VAR(Sampler_Data, ::g->Sampler_Data.generate());
	GENERATE_VAR(loops, ::g->loops.generate(Num_Sample_Loops()));
	if (((chunkSize() & 1) && !FEof(0.0))) {
		GENERATE_VAR(padding, ::g->padding.generate());
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


LISTSUBCHUNK* LISTSUBCHUNK::generate() {
	if (generated == 1) {
		LISTSUBCHUNK* new_instance = new LISTSUBCHUNK(instances);
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

	GENERATE_VAR(chunkID, ::g->chunkID.generate(4));
	size_pos = FTell();
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate());
	GENERATE_VAR(listData, ::g->listData.generate(chunkSize()));
	end = FTell();
	real_size = ((end - size_pos) - 4);
	FSeek(size_pos);
	evil = SetEvilBit(false);
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate({ real_size }));
	SetEvilBit(evil);
	FSeek(end);
	if (((chunkSize() & 1) && !FEof(0.0))) {
		GENERATE_VAR(padding, ::g->padding.generate());
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


LISTCHUNK* LISTCHUNK::generate() {
	if (generated == 1) {
		LISTCHUNK* new_instance = new LISTCHUNK(instances);
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

	GENERATE_VAR(chunkID, ::g->chunkID.generate(4));
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate());
	pos = FTell();
	list_tag.resize(1);
	GENERATE_VAR(chunkType, ::g->chunkType.generate(4));
	while (((FTell() - pos) <= (chunkSize() - 8))) {
		size = ReadUInt((FTell() + 4));
		if ((((FTell() - pos) + size) <= chunkSize())) {
			GENERATE_VAR(subchunk, ::g->subchunk.generate());
		} else {
		break;
		};
	};
	if (((FTell() - pos) < chunkSize())) {
		GENERATE_VAR(unknown, ::g->unknown.generate((chunkSize() - (FTell() - pos))));
	};
	if (((chunkSize() & 1) && !FEof(0.0))) {
		GENERATE_VAR(padding, ::g->padding.generate());
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


UNKNOWNCHUNK* UNKNOWNCHUNK::generate() {
	if (generated == 1) {
		UNKNOWNCHUNK* new_instance = new UNKNOWNCHUNK(instances);
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

	GENERATE_VAR(chunkID, ::g->chunkID.generate(4));
	GENERATE_VAR(chunkSize, ::g->chunkSize.generate());
	GENERATE_VAR(unknownData, ::g->unknownData.generate(chunkSize()));
	if (((chunkSize() & 1) && !FEof(0.0))) {
		GENERATE_VAR(padding, ::g->padding.generate());
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}



void generate_file() {
	::g = new globals_class();

	::g->haveValidFormat = false;
	::g->data_size = 0;
	LittleEndian();
	SetBackColor(cLtPurple);
	GENERATE(header, ::g->header.generate());
	if (((::g->header().groupID() != "RIFF") || (::g->header().riffType() != "WAVE"))) {
		Warning("File is not a valid wave file. Template stopped.");
		exit_template(-1);
	};
	::g->chunk_tag.resize(4);
	::g->compressed_wav = false;
	::g->tag_values_possible = { "fmt " };
	::g->tag_values_preferred = { "fmt " };
	while (ReadBytes(::g->chunk_tag, FTell(), 4, ::g->tag_values_preferred, ::g->tag_values_possible)) {
		switch (STR2INT(::g->chunk_tag)) {
		case STR2INT("fmt "):
			SetBackColor(cLtGray);
			GENERATE(format, ::g->format.generate());
			VectorRemove(::g->tag_values_preferred, { "fmt " });
			VectorRemove(::g->tag_values_possible, { "fmt " });
			::g->tag_values_preferred.insert(::g->tag_values_preferred.end(), { "data" });
			::g->tag_values_possible.insert(::g->tag_values_possible.end(), { "data" });
			break;
		case STR2INT("data"):
			SetBackColor(cNone);
			GENERATE(data, ::g->data.generate());
			VectorRemove(::g->tag_values_preferred, { "data" });
			VectorRemove(::g->tag_values_possible, { "data" });
			::g->tag_values_possible.insert(::g->tag_values_possible.end(), { "fact", "cue ", "LIST" });
			break;
		case STR2INT("fact"):
			SetBackColor(cLtBlue);
			GENERATE(fact, ::g->fact.generate());
			VectorRemove(::g->tag_values_possible, { "fact" });
			VectorRemove(::g->tag_values_preferred, { "fact" });
			break;
		case STR2INT("cue "):
			SetBackColor(cLtGray);
			GENERATE(cue, ::g->cue.generate());
			VectorRemove(::g->tag_values_preferred, { "cue " });
			VectorRemove(::g->tag_values_possible, { "cue " });
			break;
		case STR2INT("smpl"):
			SetBackColor(cLtGray);
			GENERATE(smpl, ::g->smpl.generate());
			break;
		case STR2INT("LIST"):
			SetBackColor(cLtYellow);
			GENERATE(list, ::g->list.generate());
			break;
		default:
			SetBackColor(cNone);
			GENERATE(unknown, ::g->unknown_.generate());
			break;
		};
	};
	::g->file_size = FTell();
	FSeek(4);
	GENERATE(hsize, ::g->hsize.generate({ (::g->file_size - 8) }));

	file_acc.finish();
	delete_globals();
}

void delete_globals() { delete ::g; }

