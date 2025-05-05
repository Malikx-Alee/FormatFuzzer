#include <cstdlib>
#include <cstdio>
#include <string>
#include <vector>
#include <unordered_map>
#include "bt.h"

enum compressions1bpp : DWORD {
	BI_RGB_1 = (DWORD) 0x0000,
};
std::vector<DWORD> compressions1bpp_values = { BI_RGB_1 };

typedef enum compressions1bpp E_COMPRESSIONS1BPP;
std::vector<DWORD> E_COMPRESSIONS1BPP_values = { BI_RGB_1 };

enum compressions2bpp : DWORD {
	BI_RGB_2 = (DWORD) 0x0000,
};
std::vector<DWORD> compressions2bpp_values = { BI_RGB_2 };

typedef enum compressions2bpp E_COMPRESSIONS2BPP;
std::vector<DWORD> E_COMPRESSIONS2BPP_values = { BI_RGB_2 };

enum compressions4bpp : DWORD {
	BI_RGB_4 = (DWORD) 0x0000,
	BI_RLE4_4 = (DWORD) 0x0002,
};
std::vector<DWORD> compressions4bpp_values = { BI_RGB_4, BI_RLE4_4 };

typedef enum compressions4bpp E_COMPRESSIONS4BPP;
std::vector<DWORD> E_COMPRESSIONS4BPP_values = { BI_RGB_4, BI_RLE4_4 };

enum compressions8bpp : DWORD {
	BI_RGB_8 = (DWORD) 0x0000,
	BI_RLE8_8 = (DWORD) 0x0001,
};
std::vector<DWORD> compressions8bpp_values = { BI_RGB_8, BI_RLE8_8 };

typedef enum compressions8bpp E_COMPRESSIONS8BPP;
std::vector<DWORD> E_COMPRESSIONS8BPP_values = { BI_RGB_8, BI_RLE8_8 };

enum compressions16bpp : DWORD {
	BI_RGB_16 = (DWORD) 0x0000,
};
std::vector<DWORD> compressions16bpp_values = { BI_RGB_16 };

typedef enum compressions16bpp E_COMPRESSIONS16BPP;
std::vector<DWORD> E_COMPRESSIONS16BPP_values = { BI_RGB_16 };

enum compressions24bpp : DWORD {
	BI_RGB_24 = (DWORD) 0x0000,
};
std::vector<DWORD> compressions24bpp_values = { BI_RGB_24 };

typedef enum compressions24bpp E_COMPRESSIONS24BPP;
std::vector<DWORD> E_COMPRESSIONS24BPP_values = { BI_RGB_24 };

enum compressions32bpp : DWORD {
	BI_RGB_32 = (DWORD) 0x0000,
};
std::vector<DWORD> compressions32bpp_values = { BI_RGB_32 };

typedef enum compressions32bpp E_COMPRESSIONS32BPP;
std::vector<DWORD> E_COMPRESSIONS32BPP_values = { BI_RGB_32 };

enum bpp : WORD {
	One = (WORD) 1,
	Four = (WORD) 4,
	Eight = (WORD) 8,
	Sixteen = (WORD) 16,
	Twentyfour = (WORD) 24,
	Thirtytwo = (WORD) 32,
};
std::vector<WORD> bpp_values = { One, Four, Eight, Sixteen, Twentyfour, Thirtytwo };

typedef enum bpp E_BPP;
std::vector<WORD> E_BPP_values = { One, Four, Eight, Sixteen, Twentyfour, Thirtytwo };


class CHAR_class {
	int small;
	std::vector<CHAR> known_values;
	CHAR value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(CHAR);
	CHAR operator () () { return value; }
	CHAR_class(int small, std::vector<CHAR> known_values = {}) : small(small), known_values(known_values) {}

	CHAR generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(CHAR), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(CHAR), 0, known_values);
		}
		return value;
	}

	CHAR generate(std::vector<CHAR> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(CHAR), 0, possible_values);
		return value;
	}
};



class CHAR_array_class {
	CHAR_class& element;
	std::vector<std::string> known_values;
	std::unordered_map<int, std::vector<CHAR>> element_known_values;
	std::string value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::string& operator () () { return value; }
	CHAR operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	CHAR_array_class(CHAR_class& element, std::unordered_map<int, std::vector<CHAR>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}
	CHAR_array_class(CHAR_class& element, std::vector<std::string> known_values)
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
				value.push_back(file_acc.file_integer(sizeof(CHAR), 0, known->second));
				_sizeof += sizeof(CHAR);
			}
		}
		return value;
	}
};



class DWORD_class {
	int small;
	std::vector<DWORD> known_values;
	DWORD value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(DWORD);
	DWORD operator () () { return value; }
	DWORD_class(int small, std::vector<DWORD> known_values = {}) : small(small), known_values(known_values) {}

	DWORD generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(DWORD), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(DWORD), 0, known_values);
		}
		return value;
	}

	DWORD generate(std::vector<DWORD> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(DWORD), 0, possible_values);
		return value;
	}
};



class WORD_class {
	int small;
	std::vector<WORD> known_values;
	WORD value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(WORD);
	WORD operator () () { return value; }
	WORD_class(int small, std::vector<WORD> known_values = {}) : small(small), known_values(known_values) {}

	WORD generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(WORD), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(WORD), 0, known_values);
		}
		return value;
	}

	WORD generate(std::vector<WORD> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(WORD), 0, possible_values);
		return value;
	}
};



class BITMAPFILEHEADER {
	std::vector<BITMAPFILEHEADER*>& instances;

	std::string bfType_var;
	DWORD bfSize_var;
	WORD bfReserved1_var;
	WORD bfReserved2_var;
	DWORD bfOffBits_var;

public:
	bool bfType_exists = false;
	bool bfSize_exists = false;
	bool bfReserved1_exists = false;
	bool bfReserved2_exists = false;
	bool bfOffBits_exists = false;

	std::string& bfType() {
		assert_cond(bfType_exists, "struct field bfType does not exist");
		return bfType_var;
	}
	DWORD& bfSize() {
		assert_cond(bfSize_exists, "struct field bfSize does not exist");
		return bfSize_var;
	}
	WORD& bfReserved1() {
		assert_cond(bfReserved1_exists, "struct field bfReserved1 does not exist");
		return bfReserved1_var;
	}
	WORD& bfReserved2() {
		assert_cond(bfReserved2_exists, "struct field bfReserved2 does not exist");
		return bfReserved2_var;
	}
	DWORD& bfOffBits() {
		assert_cond(bfOffBits_exists, "struct field bfOffBits does not exist");
		return bfOffBits_var;
	}

	/* locals */
	int evil;

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	BITMAPFILEHEADER& operator () () { return *instances.back(); }
	BITMAPFILEHEADER& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	BITMAPFILEHEADER(std::vector<BITMAPFILEHEADER*>& instances) : instances(instances) { instances.push_back(this); }
	~BITMAPFILEHEADER() {
		if (generated == 2)
			return;
		while (instances.size()) {
			BITMAPFILEHEADER* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	BITMAPFILEHEADER* generate();
};

int BITMAPFILEHEADER::_parent_id = 0;
int BITMAPFILEHEADER::_index_start = 0;



class LONG_class {
	int small;
	std::vector<LONG> known_values;
	LONG value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(LONG);
	LONG operator () () { return value; }
	LONG_class(int small, std::vector<LONG> known_values = {}) : small(small), known_values(known_values) {}

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


E_BPP E_BPP_generate() {
	return (E_BPP) file_acc.file_integer(sizeof(WORD), 0, E_BPP_values);
}

E_BPP E_BPP_generate(std::vector<WORD> known_values) {
	return (E_BPP) file_acc.file_integer(sizeof(WORD), 0, known_values);
}

E_COMPRESSIONS1BPP E_COMPRESSIONS1BPP_generate() {
	return (E_COMPRESSIONS1BPP) file_acc.file_integer(sizeof(DWORD), 0, E_COMPRESSIONS1BPP_values);
}

E_COMPRESSIONS1BPP E_COMPRESSIONS1BPP_generate(std::vector<DWORD> known_values) {
	return (E_COMPRESSIONS1BPP) file_acc.file_integer(sizeof(DWORD), 0, known_values);
}

E_COMPRESSIONS2BPP E_COMPRESSIONS2BPP_generate() {
	return (E_COMPRESSIONS2BPP) file_acc.file_integer(sizeof(DWORD), 0, E_COMPRESSIONS2BPP_values);
}

E_COMPRESSIONS2BPP E_COMPRESSIONS2BPP_generate(std::vector<DWORD> known_values) {
	return (E_COMPRESSIONS2BPP) file_acc.file_integer(sizeof(DWORD), 0, known_values);
}

E_COMPRESSIONS4BPP E_COMPRESSIONS4BPP_generate() {
	return (E_COMPRESSIONS4BPP) file_acc.file_integer(sizeof(DWORD), 0, E_COMPRESSIONS4BPP_values);
}

E_COMPRESSIONS4BPP E_COMPRESSIONS4BPP_generate(std::vector<DWORD> known_values) {
	return (E_COMPRESSIONS4BPP) file_acc.file_integer(sizeof(DWORD), 0, known_values);
}

E_COMPRESSIONS8BPP E_COMPRESSIONS8BPP_generate() {
	return (E_COMPRESSIONS8BPP) file_acc.file_integer(sizeof(DWORD), 0, E_COMPRESSIONS8BPP_values);
}

E_COMPRESSIONS8BPP E_COMPRESSIONS8BPP_generate(std::vector<DWORD> known_values) {
	return (E_COMPRESSIONS8BPP) file_acc.file_integer(sizeof(DWORD), 0, known_values);
}

E_COMPRESSIONS16BPP E_COMPRESSIONS16BPP_generate() {
	return (E_COMPRESSIONS16BPP) file_acc.file_integer(sizeof(DWORD), 0, E_COMPRESSIONS16BPP_values);
}

E_COMPRESSIONS16BPP E_COMPRESSIONS16BPP_generate(std::vector<DWORD> known_values) {
	return (E_COMPRESSIONS16BPP) file_acc.file_integer(sizeof(DWORD), 0, known_values);
}

E_COMPRESSIONS24BPP E_COMPRESSIONS24BPP_generate() {
	return (E_COMPRESSIONS24BPP) file_acc.file_integer(sizeof(DWORD), 0, E_COMPRESSIONS24BPP_values);
}

E_COMPRESSIONS24BPP E_COMPRESSIONS24BPP_generate(std::vector<DWORD> known_values) {
	return (E_COMPRESSIONS24BPP) file_acc.file_integer(sizeof(DWORD), 0, known_values);
}

E_COMPRESSIONS32BPP E_COMPRESSIONS32BPP_generate() {
	return (E_COMPRESSIONS32BPP) file_acc.file_integer(sizeof(DWORD), 0, E_COMPRESSIONS32BPP_values);
}

E_COMPRESSIONS32BPP E_COMPRESSIONS32BPP_generate(std::vector<DWORD> known_values) {
	return (E_COMPRESSIONS32BPP) file_acc.file_integer(sizeof(DWORD), 0, known_values);
}


class BITMAPINFOHEADER {
	std::vector<BITMAPINFOHEADER*>& instances;

	DWORD biSize_var;
	LONG biWidth_var;
	LONG biHeight_var;
	WORD biPlanes_var;
	WORD biBitCount_var;
	DWORD biCompression_var;
	DWORD biSizeImage_var;
	LONG biXPelsPerMeter_var;
	LONG biYPelsPerMeter_var;
	DWORD biClrUsed_var;
	DWORD biClrImportant_var;

public:
	bool biSize_exists = false;
	bool biWidth_exists = false;
	bool biHeight_exists = false;
	bool biPlanes_exists = false;
	bool biBitCount_exists = false;
	bool biCompression_exists = false;
	bool biSizeImage_exists = false;
	bool biXPelsPerMeter_exists = false;
	bool biYPelsPerMeter_exists = false;
	bool biClrUsed_exists = false;
	bool biClrImportant_exists = false;

	DWORD& biSize() {
		assert_cond(biSize_exists, "struct field biSize does not exist");
		return biSize_var;
	}
	LONG& biWidth() {
		assert_cond(biWidth_exists, "struct field biWidth does not exist");
		return biWidth_var;
	}
	LONG& biHeight() {
		assert_cond(biHeight_exists, "struct field biHeight does not exist");
		return biHeight_var;
	}
	WORD& biPlanes() {
		assert_cond(biPlanes_exists, "struct field biPlanes does not exist");
		return biPlanes_var;
	}
	WORD& biBitCount() {
		assert_cond(biBitCount_exists, "struct field biBitCount does not exist");
		return biBitCount_var;
	}
	DWORD& biCompression() {
		assert_cond(biCompression_exists, "struct field biCompression does not exist");
		return biCompression_var;
	}
	DWORD& biSizeImage() {
		assert_cond(biSizeImage_exists, "struct field biSizeImage does not exist");
		return biSizeImage_var;
	}
	LONG& biXPelsPerMeter() {
		assert_cond(biXPelsPerMeter_exists, "struct field biXPelsPerMeter does not exist");
		return biXPelsPerMeter_var;
	}
	LONG& biYPelsPerMeter() {
		assert_cond(biYPelsPerMeter_exists, "struct field biYPelsPerMeter does not exist");
		return biYPelsPerMeter_var;
	}
	DWORD& biClrUsed() {
		assert_cond(biClrUsed_exists, "struct field biClrUsed does not exist");
		return biClrUsed_var;
	}
	DWORD& biClrImportant() {
		assert_cond(biClrImportant_exists, "struct field biClrImportant does not exist");
		return biClrImportant_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	BITMAPINFOHEADER& operator () () { return *instances.back(); }
	BITMAPINFOHEADER& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	BITMAPINFOHEADER(std::vector<BITMAPINFOHEADER*>& instances) : instances(instances) { instances.push_back(this); }
	~BITMAPINFOHEADER() {
		if (generated == 2)
			return;
		while (instances.size()) {
			BITMAPINFOHEADER* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	BITMAPINFOHEADER* generate();
};

int BITMAPINFOHEADER::_parent_id = 0;
int BITMAPINFOHEADER::_index_start = 0;



class UBYTE_class {
	int small;
	std::vector<UBYTE> known_values;
	UBYTE value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = sizeof(UBYTE);
	UBYTE operator () () { return value; }
	UBYTE_class(int small, std::vector<UBYTE> known_values = {}) : small(small), known_values(known_values) {}

	UBYTE generate() {
		_startof = FTell();
		if (known_values.empty()) {
			value = file_acc.file_integer(sizeof(UBYTE), 0, small);
		} else {
			value = file_acc.file_integer(sizeof(UBYTE), 0, known_values);
		}
		return value;
	}

	UBYTE generate(std::vector<UBYTE> possible_values) {
		_startof = FTell();
		value = file_acc.file_integer(sizeof(UBYTE), 0, possible_values);
		return value;
	}
};



class RGBQUAD {
	std::vector<RGBQUAD*>& instances;

	UBYTE rgbBlue_var;
	UBYTE rgbGreen_var;
	UBYTE rgbRed_var;
	UBYTE rgbReserved_var;

public:
	bool rgbBlue_exists = false;
	bool rgbGreen_exists = false;
	bool rgbRed_exists = false;
	bool rgbReserved_exists = false;

	UBYTE& rgbBlue() {
		assert_cond(rgbBlue_exists, "struct field rgbBlue does not exist");
		return rgbBlue_var;
	}
	UBYTE& rgbGreen() {
		assert_cond(rgbGreen_exists, "struct field rgbGreen does not exist");
		return rgbGreen_var;
	}
	UBYTE& rgbRed() {
		assert_cond(rgbRed_exists, "struct field rgbRed does not exist");
		return rgbRed_var;
	}
	UBYTE& rgbReserved() {
		assert_cond(rgbReserved_exists, "struct field rgbReserved does not exist");
		return rgbReserved_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	RGBQUAD& operator () () { return *instances.back(); }
	RGBQUAD& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	RGBQUAD(std::vector<RGBQUAD*>& instances) : instances(instances) { instances.push_back(this); }
	~RGBQUAD() {
		if (generated == 2)
			return;
		while (instances.size()) {
			RGBQUAD* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	RGBQUAD* generate();
};

int RGBQUAD::_parent_id = 0;
int RGBQUAD::_index_start = 0;



class RGBQUAD_array_class {
	RGBQUAD& element;
	std::vector<RGBQUAD*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<RGBQUAD*>& operator () () { return value; }
	RGBQUAD operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	RGBQUAD_array_class(RGBQUAD& element) : element(element) {}

	std::vector<RGBQUAD*> generate(unsigned size) {
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



class UBYTE_array_class {
	UBYTE_class& element;
	std::unordered_map<int, std::vector<UBYTE>> element_known_values;
	std::vector<UBYTE> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<UBYTE>& operator () () { return value; }
	UBYTE operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return value[index];
	}
	UBYTE_array_class(UBYTE_class& element, std::unordered_map<int, std::vector<UBYTE>> element_known_values = {})
		: element(element), element_known_values(element_known_values) {}

	std::vector<UBYTE> generate(unsigned size) {
		check_array_length(size);
		_startof = FTell();
		value = {};
		for (unsigned i = 0; i < size; ++i) {
			auto known = element_known_values.find(i);
			if (known == element_known_values.end()) {
				value.push_back(element.generate());
				_sizeof += element._sizeof;
			} else {
				value.push_back(file_acc.file_integer(sizeof(UBYTE), 0, known->second));
				_sizeof += sizeof(UBYTE);
			}
		}
		return value;
	}
};



class RGBALPHA {
	std::vector<RGBALPHA*>& instances;

	UBYTE rgbBlue_var;
	UBYTE rgbGreen_var;
	UBYTE rgbRed_var;
	UBYTE alphamaskFlag_var;

public:
	bool rgbBlue_exists = false;
	bool rgbGreen_exists = false;
	bool rgbRed_exists = false;
	bool alphamaskFlag_exists = false;

	UBYTE& rgbBlue() {
		assert_cond(rgbBlue_exists, "struct field rgbBlue does not exist");
		return rgbBlue_var;
	}
	UBYTE& rgbGreen() {
		assert_cond(rgbGreen_exists, "struct field rgbGreen does not exist");
		return rgbGreen_var;
	}
	UBYTE& rgbRed() {
		assert_cond(rgbRed_exists, "struct field rgbRed does not exist");
		return rgbRed_var;
	}
	UBYTE& alphamaskFlag() {
		assert_cond(alphamaskFlag_exists, "struct field alphamaskFlag does not exist");
		return alphamaskFlag_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	RGBALPHA& operator () () { return *instances.back(); }
	RGBALPHA& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	RGBALPHA(std::vector<RGBALPHA*>& instances) : instances(instances) { instances.push_back(this); }
	~RGBALPHA() {
		if (generated == 2)
			return;
		while (instances.size()) {
			RGBALPHA* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	RGBALPHA* generate();
};

int RGBALPHA::_parent_id = 0;
int RGBALPHA::_index_start = 0;



class RGBALPHA_array_class {
	RGBALPHA& element;
	std::vector<RGBALPHA*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<RGBALPHA*>& operator () () { return value; }
	RGBALPHA operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	RGBALPHA_array_class(RGBALPHA& element) : element(element) {}

	std::vector<RGBALPHA*> generate(unsigned size) {
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



class RGBTRIPLE {
	std::vector<RGBTRIPLE*>& instances;

	UBYTE rgbBlue_var;
	UBYTE rgbGreen_var;
	UBYTE rgbRed_var;

public:
	bool rgbBlue_exists = false;
	bool rgbGreen_exists = false;
	bool rgbRed_exists = false;

	UBYTE& rgbBlue() {
		assert_cond(rgbBlue_exists, "struct field rgbBlue does not exist");
		return rgbBlue_var;
	}
	UBYTE& rgbGreen() {
		assert_cond(rgbGreen_exists, "struct field rgbGreen does not exist");
		return rgbGreen_var;
	}
	UBYTE& rgbRed() {
		assert_cond(rgbRed_exists, "struct field rgbRed does not exist");
		return rgbRed_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	RGBTRIPLE& operator () () { return *instances.back(); }
	RGBTRIPLE& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	RGBTRIPLE(std::vector<RGBTRIPLE*>& instances) : instances(instances) { instances.push_back(this); }
	~RGBTRIPLE() {
		if (generated == 2)
			return;
		while (instances.size()) {
			RGBTRIPLE* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	RGBTRIPLE* generate();
};

int RGBTRIPLE::_parent_id = 0;
int RGBTRIPLE::_index_start = 0;



class RGBTRIPLE_array_class {
	RGBTRIPLE& element;
	std::vector<RGBTRIPLE*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<RGBTRIPLE*>& operator () () { return value; }
	RGBTRIPLE operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	RGBTRIPLE_array_class(RGBTRIPLE& element) : element(element) {}

	std::vector<RGBTRIPLE*> generate(unsigned size) {
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



class BITMAPLINE {
	std::vector<BITMAPLINE*>& instances;

	std::vector<UBYTE> imageData_var;
	std::vector<UBYTE> colorIndex_var;
	std::vector<UBYTE> padBytes_var;

public:
	bool imageData_exists = false;
	bool colorIndex_exists = false;
	bool padBytes_exists = false;

	std::vector<UBYTE>& imageData() {
		assert_cond(imageData_exists, "struct field imageData does not exist");
		return imageData_var;
	}
	std::vector<UBYTE>& colorIndex() {
		assert_cond(colorIndex_exists, "struct field colorIndex does not exist");
		return colorIndex_var;
	}
	std::vector<UBYTE>& padBytes() {
		assert_cond(padBytes_exists, "struct field padBytes does not exist");
		return padBytes_var;
	}

	unsigned char generated = 0;
	static int _parent_id;
	static int _index_start;
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	BITMAPLINE& operator () () { return *instances.back(); }
	BITMAPLINE& operator [] (int index) {
		assert_cond((unsigned)(_index_start + index) < instances.size(), "instance index out of bounds");
		return *instances[_index_start + index];
	}
	std::size_t array_size() {
		return instances.size() - _index_start;
	}
	BITMAPLINE(std::vector<BITMAPLINE*>& instances) : instances(instances) { instances.push_back(this); }
	~BITMAPLINE() {
		if (generated == 2)
			return;
		while (instances.size()) {
			BITMAPLINE* instance = instances.back();
			instances.pop_back();
			if (instance->generated == 2)
				delete instance;
		}
	}
	BITMAPLINE* generate();
};

int BITMAPLINE::_parent_id = 0;
int BITMAPLINE::_index_start = 0;



class BITMAPLINE_array_class {
	BITMAPLINE& element;
	std::vector<BITMAPLINE*> value;
public:
	int64 _startof = 0;
	std::size_t _sizeof = 0;
	std::vector<BITMAPLINE*>& operator () () { return value; }
	BITMAPLINE operator [] (int index) {
		assert_cond((unsigned)index < value.size(), "array index out of bounds");
		return *value[index];
	}
	BITMAPLINE_array_class(BITMAPLINE& element) : element(element) {}

	std::vector<BITMAPLINE*> generate(unsigned size) {
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
std::vector<std::string> ReadBytesInitValues;


std::vector<BITMAPFILEHEADER*> BITMAPFILEHEADER_bmfh_instances;
std::vector<BITMAPINFOHEADER*> BITMAPINFOHEADER_bmih_instances;
std::vector<RGBQUAD*> RGBQUAD_aColors_element_instances;
std::vector<RGBALPHA*> RGBALPHA_colors_element_instances;
std::vector<RGBTRIPLE*> RGBTRIPLE_colors__element_instances;
std::vector<RGBQUAD*> RGBQUAD_colors___element_instances;
std::vector<BITMAPLINE*> BITMAPLINE_lines_element_instances;


std::unordered_map<std::string, std::string> variable_types = { { "bfType", "CHAR_array_class" }, { "bfSize", "DWORD_class" }, { "bfReserved1", "WORD_class" }, { "bfReserved2", "WORD_class" }, { "bfOffBits", "DWORD_class" }, { "bmfh", "BITMAPFILEHEADER" }, { "biSize", "DWORD_class" }, { "biWidth", "LONG_class" }, { "biHeight", "LONG_class" }, { "biPlanes", "WORD_class" }, { "biBitCount", "E_BPP" }, { "biCompression", "E_COMPRESSIONS32BPP" }, { "biSizeImage", "DWORD_class" }, { "biXPelsPerMeter", "LONG_class" }, { "biYPelsPerMeter", "LONG_class" }, { "biClrUsed", "DWORD_class" }, { "biClrImportant", "DWORD_class" }, { "bmih", "BITMAPINFOHEADER" }, { "rgbBlue", "UBYTE_class" }, { "rgbGreen", "UBYTE_class" }, { "rgbRed", "UBYTE_class" }, { "rgbReserved", "UBYTE_class" }, { "aColors", "RGBQUAD_array_class" }, { "real_offset", "DWORD_class" }, { "rleData", "UBYTE_array_class" }, { "imageData", "UBYTE_array_class" }, { "colorIndex", "UBYTE_array_class" }, { "alphamaskFlag", "UBYTE_class" }, { "colors", "RGBALPHA_array_class" }, { "colors_", "RGBTRIPLE_array_class" }, { "colors__", "RGBQUAD_array_class" }, { "padBytes", "UBYTE_array_class" }, { "lines", "BITMAPLINE_array_class" }, { "real_hsize", "LONG_class" } };

std::vector<std::vector<int>> integer_ranges = { { 1, 16 }, { 1, INT_MAX }, { 1, INT_MAX }, { 0, 256 } };

class globals_class {
public:
	int _struct_id = 0;
	int _struct_id_counter = 0;
	CHAR_class bfType_element;
	CHAR_array_class bfType;
	DWORD_class bfSize;
	WORD_class bfReserved1;
	WORD_class bfReserved2;
	DWORD_class bfOffBits;
	BITMAPFILEHEADER bmfh;
	DWORD_class biSize;
	LONG_class biWidth;
	LONG_class biHeight;
	WORD_class biPlanes;
	DWORD_class biSizeImage;
	LONG_class biXPelsPerMeter;
	LONG_class biYPelsPerMeter;
	DWORD_class biClrUsed;
	DWORD_class biClrImportant;
	BITMAPINFOHEADER bmih;
	UBYTE_class rgbBlue;
	UBYTE_class rgbGreen;
	UBYTE_class rgbRed;
	UBYTE_class rgbReserved;
	RGBQUAD aColors_element;
	RGBQUAD_array_class aColors;
	/*local*/ int evil;
	/*local*/ DWORD current_pos;
	DWORD_class real_offset;
	UBYTE_class rleData_element;
	UBYTE_array_class rleData;
	UBYTE_class imageData_element;
	UBYTE_array_class imageData;
	UBYTE_class colorIndex_element;
	UBYTE_array_class colorIndex;
	UBYTE_class alphamaskFlag;
	RGBALPHA colors_element;
	RGBALPHA_array_class colors;
	RGBTRIPLE colors__element;
	RGBTRIPLE_array_class colors_;
	RGBQUAD colors___element;
	RGBQUAD_array_class colors__;
	UBYTE_class padBytes_element;
	UBYTE_array_class padBytes;
	BITMAPLINE lines_element;
	BITMAPLINE_array_class lines;
	/*local*/ int bytesPerLine;
	/*local*/ int padding;
	/*local*/ int file_size;
	LONG_class real_hsize;


	globals_class() :
		bfType_element(false),
		bfType(bfType_element, { "BM" }),
		bfSize(1),
		bfReserved1(1),
		bfReserved2(1),
		bfOffBits(1),
		bmfh(BITMAPFILEHEADER_bmfh_instances),
		biSize(1),
		biWidth(3),
		biHeight(4),
		biPlanes(1),
		biSizeImage(1),
		biXPelsPerMeter(1),
		biYPelsPerMeter(1),
		biClrUsed(5),
		biClrImportant(1),
		bmih(BITMAPINFOHEADER_bmih_instances),
		rgbBlue(1),
		rgbGreen(1),
		rgbRed(1),
		rgbReserved(1),
		aColors_element(RGBQUAD_aColors_element_instances),
		aColors(aColors_element),
		real_offset(1),
		rleData_element(false),
		rleData(rleData_element),
		imageData_element(false),
		imageData(imageData_element),
		colorIndex_element(false),
		colorIndex(colorIndex_element),
		alphamaskFlag(1),
		colors_element(RGBALPHA_colors_element_instances),
		colors(colors_element),
		colors__element(RGBTRIPLE_colors__element_instances),
		colors_(colors__element),
		colors___element(RGBQUAD_colors___element_instances),
		colors__(colors___element),
		padBytes_element(false),
		padBytes(padBytes_element),
		lines_element(BITMAPLINE_lines_element_instances),
		lines(lines_element),
		real_hsize(1)
	{}
};

globals_class* g;


BITMAPFILEHEADER* BITMAPFILEHEADER::generate() {
	if (generated == 1) {
		BITMAPFILEHEADER* new_instance = new BITMAPFILEHEADER(instances);
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

	evil = SetEvilBit(false);
	GENERATE_VAR(bfType, ::g->bfType.generate(2, { "BM" }));
	SetEvilBit(evil);
	GENERATE_VAR(bfSize, ::g->bfSize.generate());
	GENERATE_VAR(bfReserved1, ::g->bfReserved1.generate({ 0x0 }));
	GENERATE_VAR(bfReserved2, ::g->bfReserved2.generate({ 0x0 }));
	GENERATE_VAR(bfOffBits, ::g->bfOffBits.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


BITMAPINFOHEADER* BITMAPINFOHEADER::generate() {
	if (generated == 1) {
		BITMAPINFOHEADER* new_instance = new BITMAPINFOHEADER(instances);
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

	GENERATE_VAR(biSize, ::g->biSize.generate({ 40 }));
	GENERATE_VAR(biWidth, ::g->biWidth.generate());
	GENERATE_VAR(biHeight, ::g->biHeight.generate());
	GENERATE_VAR(biPlanes, ::g->biPlanes.generate({ 1 }));
	GENERATE_VAR(biBitCount, E_BPP_generate());
	if ((biBitCount() == 1)) {
		GENERATE_VAR(biCompression, E_COMPRESSIONS1BPP_generate());
	};
	if ((biBitCount() == 2)) {
		GENERATE_VAR(biCompression, E_COMPRESSIONS2BPP_generate());
	};
	if ((biBitCount() == 4)) {
		GENERATE_VAR(biCompression, E_COMPRESSIONS4BPP_generate());
	};
	if ((biBitCount() == 8)) {
		GENERATE_VAR(biCompression, E_COMPRESSIONS8BPP_generate());
	};
	if ((biBitCount() == 16)) {
		GENERATE_VAR(biCompression, E_COMPRESSIONS16BPP_generate());
	};
	if ((biBitCount() == 24)) {
		GENERATE_VAR(biCompression, E_COMPRESSIONS24BPP_generate());
	};
	if ((biBitCount() == 32)) {
		GENERATE_VAR(biCompression, E_COMPRESSIONS32BPP_generate());
	};
	if (((biCompression() == 0) || (biCompression() == 11))) {
		GENERATE_VAR(biSizeImage, ::g->biSizeImage.generate({ 0 }));
	} else {
		GENERATE_VAR(biSizeImage, ::g->biSizeImage.generate());
	};
	GENERATE_VAR(biXPelsPerMeter, ::g->biXPelsPerMeter.generate({ 0 }));
	GENERATE_VAR(biYPelsPerMeter, ::g->biYPelsPerMeter.generate({ 0 }));
	switch (biBitCount()) {
	case 8:
		GENERATE_VAR(biClrUsed, ::g->biClrUsed.generate());
		break;
	case 4:
		GENERATE_VAR(biClrUsed, ::g->biClrUsed.generate({ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 }));
		break;
	case 2:
		GENERATE_VAR(biClrUsed, ::g->biClrUsed.generate({ 0, 1, 2, 3, 4 }));
		break;
	case 1:
		GENERATE_VAR(biClrUsed, ::g->biClrUsed.generate({ 0, 1, 2 }));
		break;
	default:
		GENERATE_VAR(biClrUsed, ::g->biClrUsed.generate({ 0 }));
	};
	GENERATE_VAR(biClrImportant, ::g->biClrImportant.generate({ 0 }));

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


RGBQUAD* RGBQUAD::generate() {
	if (generated == 1) {
		RGBQUAD* new_instance = new RGBQUAD(instances);
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

	GENERATE_VAR(rgbBlue, ::g->rgbBlue.generate());
	GENERATE_VAR(rgbGreen, ::g->rgbGreen.generate());
	GENERATE_VAR(rgbRed, ::g->rgbRed.generate());
	GENERATE_VAR(rgbReserved, ::g->rgbReserved.generate({ 0 }));

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


RGBALPHA* RGBALPHA::generate() {
	if (generated == 1) {
		RGBALPHA* new_instance = new RGBALPHA(instances);
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

	GENERATE_VAR(rgbBlue, ::g->rgbBlue.generate());
	GENERATE_VAR(rgbGreen, ::g->rgbGreen.generate());
	GENERATE_VAR(rgbRed, ::g->rgbRed.generate());
	GENERATE_VAR(alphamaskFlag, ::g->alphamaskFlag.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


RGBTRIPLE* RGBTRIPLE::generate() {
	if (generated == 1) {
		RGBTRIPLE* new_instance = new RGBTRIPLE(instances);
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

	GENERATE_VAR(rgbBlue, ::g->rgbBlue.generate());
	GENERATE_VAR(rgbGreen, ::g->rgbGreen.generate());
	GENERATE_VAR(rgbRed, ::g->rgbRed.generate());

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}


BITMAPLINE* BITMAPLINE::generate() {
	if (generated == 1) {
		BITMAPLINE* new_instance = new BITMAPLINE(instances);
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

	if ((::g->bmih().biBitCount() < 8)) {
		GENERATE_VAR(imageData, ::g->imageData.generate(::g->bytesPerLine));
	} else {
	if ((::g->bmih().biBitCount() == 8)) {
		GENERATE_VAR(colorIndex, ::g->colorIndex.generate(::g->bmih().biWidth()));
	} else {
	if ((::g->bmih().biBitCount() == 16)) {
		GENERATE(colors, ::g->colors.generate(::g->bmih().biWidth()));
	} else {
	if ((::g->bmih().biBitCount() == 24)) {
		GENERATE(colors, ::g->colors_.generate(::g->bmih().biWidth()));
	} else {
	if ((::g->bmih().biBitCount() == 32)) {
		GENERATE(colors, ::g->colors__.generate(::g->bmih().biWidth()));
	};
	};
	};
	};
	};
	if ((::g->padding != 0)) {
		GENERATE_VAR(padBytes, ::g->padBytes.generate(::g->padding));
	};

	::g->_struct_id = _parent_id;
	_sizeof = FTell() - _startof;
	return this;
}



void generate_file() {
	::g = new globals_class();

	LittleEndian();
	SetBackColor(cLtGray);
	GENERATE(bmfh, ::g->bmfh.generate());
	GENERATE(bmih, ::g->bmih.generate());
	if ((::g->bmfh().bfType() != "BM")) {
		Warning("File is not a bitmap. Template stopped.");
		exit_template(-1);
	};
	if ((((::g->bmih().biBitCount() != 16) && (::g->bmih().biBitCount() != 24)) && (::g->bmih().biBitCount() != 32))) {
		SetBackColor(cLtAqua);
		if ((::g->bmih().biClrUsed() > 0)) {
			GENERATE(aColors, ::g->aColors.generate(::g->bmih().biClrUsed()));
		} else {
			GENERATE(aColors, ::g->aColors.generate((1 << ::g->bmih().biBitCount())));
		};
	};
	::g->evil = SetEvilBit(false);
	::g->current_pos = FTell();
	FSeek(10);
	GENERATE(real_offset, ::g->real_offset.generate({ ::g->current_pos }));
	FSeek(::g->current_pos);
	SetEvilBit(::g->evil);
	SetBackColor(cNone);
	if ((::g->bmih().biCompression() > 0)) {
		if ((::g->bmih().biSizeImage() > 0)) {
			GENERATE(rleData, ::g->rleData.generate(::g->bmih().biSizeImage()));
		} else {
			GENERATE(rleData, ::g->rleData.generate((::g->bmfh().bfSize() - FTell())));
		};
	} else {
		::g->bytesPerLine = (((::g->bmih().biWidth() * ::g->bmih().biBitCount()) + 7) / 8);
		::g->padding = (4 - (::g->bytesPerLine % 4));
		if ((::g->padding == 4)) {
		::g->padding = 0;
		};
		GENERATE(lines, ::g->lines.generate(((::g->bmih().biHeight() < 0) ? -::g->bmih().biHeight() : ::g->bmih().biHeight())));
	};
	::g->evil = SetEvilBit(false);
	::g->file_size = FTell();
	FSeek(2);
	GENERATE(real_hsize, ::g->real_hsize.generate({ ::g->file_size }));

	file_acc.finish();
	delete_globals();
}

void delete_globals() { delete ::g; }

