/*
 * Common functions that may be useful for different analyses.
 * author: Carlos Vico (carlos.vico.villalba@cern.ch)
 */

#ifndef COMMON_FUNCTIONS_H
#define COMMON_FUNCTIONS_H

#include <ROOT/RVec.hxx>
#include "functions.h"
#include <iostream>
#include <string>
#include <cstdarg>
#include <cstdio>


ROOT::RVec<bool> get_first_copy ( const ROOT::RVec<int>, const ROOT::RVec<int>, const ROOT::RVec<bool> );

template <typename T>
ROOT::RVec<T> get_parents_properties(
    const ROOT::RVec<int>& startIdx,
    const ROOT::RVec<int>& motherIdx,
    const ROOT::RVec<T>& input_properties,
    int N)
{
    ROOT::RVec<T> parents_properties(startIdx.size());
    for (int i = 0; i < (int)startIdx.size(); i++) {
        int idx = startIdx[i];
        for (int level = 0; level < N; level++) {
            if (idx < 0 || idx >= (int)motherIdx.size()) {
                idx = -1;
                break;
            }
            idx = motherIdx[idx];
        }
        if (idx >= 0 && idx < (int)input_properties.size())
            parents_properties[i] = input_properties[idx];
        else
            parents_properties[i] = T(0);
    }
    return parents_properties;
}

// --------------------------------------------
// get_all_ancestors_properties
// --------------------------------------------
template <typename T>
ROOT::RVec<T> get_all_ancestors_properties(
    const int seed_idx,
    const ROOT::RVec<int>& parentIdx,
    const ROOT::RVec<T>& input_properties)
{
    int idx = seed_idx;
    ROOT::RVec<T> properties;
    while (idx >= 0 && idx < (int)parentIdx.size()) {
        properties.push_back(input_properties[idx]);
        idx = parentIdx[idx];
    }
    return properties;
}

// Simple printf-style formatter
inline std::string vformat(const char* fmt, va_list args) {
    char buf[512];
    vsnprintf(buf, sizeof(buf), fmt, args);
    return std::string(buf);
}

inline std::string format(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    std::string s = vformat(fmt, args);
    va_end(args);
    return s;
}

// Logger with f-string formatting (kind of)
inline void log(int indentLevel, const char* fmt, ...) {
    #ifdef _DEBUGCOMB
        va_list args;
        va_start(args, fmt);
        std::string msg = vformat(fmt, args);
        va_end(args);
        int indent = indentLevel * 2;
        std::cout << std::string(indent, ' ') << "+ " << msg << std::endl;
    #else
        (void)indentLevel; (void)fmt;
    #endif
}


// --- Templated loglist() ---
template <typename T>
inline void loglist(int indentLevel, const ROOT::RVec<T>& list) {
    #ifdef _DEBUGCOMB
        std::ostringstream msg;
        msg << "[ ";
        for (size_t i = 0; i < list.size(); ++i) {
            msg << list[i];
            if (i + 1 < list.size()) msg << ", ";
        }
        msg << " ]";
        std::string tmp = msg.str();
        log(indentLevel, tmp.c_str());
    #else
        (void)indentLevel; (void)list;
    #endif
}


#endif // COMMON_FUNCTIONS_H

