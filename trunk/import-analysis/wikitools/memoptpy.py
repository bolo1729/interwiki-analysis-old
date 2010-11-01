#!/usr/bin/env python

# Copyright 2010 Lukasz Bolikowski. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
# 
#    1. Redistributions of source code must retain the above copyright notice, this list of
#       conditions and the following disclaimer.
# 
#    2. Redistributions in binary form must reproduce the above copyright notice, this list
#       of conditions and the following disclaimer in the documentation and/or other materials
#       provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY LUKASZ BOLIKOWSKI ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LUKASZ BOLIKOWSKI OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""This module contains various memory-optimized data structures."""

import array

class IntSet:
	"""A set of integers.  Implemented using a dictionary of integer arrays."""

	BLOCKBITS = 16

	def __init__(self, iterable = []):
		"""Initializes the set.  Examples:
		>>> s = IntSet()
		>>> s = IntSet([0, 1, 8])
		>>> s = IntSet(set([0, 1, 8]))
		"""
		self.__blocks = {}
		for item in iterable:
			self.add(item)

	def __getpos(self, elem):
		high, low = elem >> self.BLOCKBITS, elem % (1 << self.BLOCKBITS)
		if not high in self.__blocks:
			self.__blocks[high] = array.array('i')
		block = self.__blocks[high]
		n = len(block)
		l, r = 0, n
		while l < r:
			m = l + (r - l) // 2
			t = block[m]
			if t == elem:
				return high, m
			if t < elem:
				l = m + 1
			else:
				r = m
		return high, l

	def add(self, elem):
		"""Adds an element to the set.  Examples:
		>>> s = IntSet([0, 1, 8])
		>>> len(s)
		3
		>>> s.add(8)
		>>> len(s)
		3
		>>> 27 in s
		False
		>>> s.add(27)
		>>> 27 in s
		True
		"""
		b, p = self.__getpos(elem)
		block = self.__blocks[b]
		n = len(block)
		if p == n:
			block.append(elem)
		elif block[p] <> elem:
			block.insert(p, elem)

	def remove(self, elem):
		"""Removes an element from the set.  Examples:
		>>> s = IntSet([0, 1, 8])
		>>> 0 in s
		True
		>>> s.remove(0)
		>>> 0 in s
		False
		>>> s.remove(-1)
		Traceback (most recent call last):
			...
		KeyError: -1
		"""
		b, p = self.__getpos(elem)
		block = self.__blocks[b]
		n = len(block)
		if p == n or block[p] <> elem:
			raise KeyError, elem
		block.pop(p)

	def __contains__(self, elem):
		"""Tests whether an element is in the set.  Examples:
		>>> s = IntSet([0, 1, 8])
		>>> 0 in s
		True
		>>> -1 in s
		False
		"""
		b, p = self.__getpos(elem)
		block = self.__blocks[b]
		n = len(block)
		if p == n:
			return False
		return block[p] == elem

	def __iter__(self):
		"""Iterates over the elements of the set.  Examples:
		>>> s = IntSet([0, 1, 8])
		>>> t = 0
		>>> for e in s: t += e
		>>> t
		9
		"""
		for b in self.__blocks:
			block = self.__blocks[b]
			n = len(block)
			for p in xrange(n):
				yield block[p]

	def __len__(self):
		"""Returns the number of elements in the set.  Examples:
		>>> s = IntSet([0, 1, 8])
		>>> len(s)
		3
		"""
		result = 0
		for b in self.__blocks:
			result += len(self.__blocks[b])
		return result

	def __repr__(self):
		"""Returns the "official" string representation of the set."""
		return 'IntSet(' + str(self) + ')'

	def __str__(self):
		"""Returns an "informal" string representation of the set."""
		result, count = '', 0
		for elem in self:
			if count > 0:
				result += ', '
			if count == 100:
				result += '...'
				break
			result += str(elem)
			count += 1
		return '[' + result + ']'

class IntIntDict:
	"""A dictionary with integer keys and values.
	Implemented using a dictionary of integer arrays.
	"""

	BLOCKBITS = 16

	def __init__(self, dictionary = {}):
		"""Initializes the dictionary.  Examples:
		>>> d = IntIntDict()
		>>> d = IntIntDict({0: 0, 1: -1, 8: -2})
		"""
		self.__blocks = {}
		for key in dictionary:
			self[key] = dictionary[key]

	def __getpos(self, key):
		"""Returns a block and a position within the block where
		the given key should be.  If a different key is present
		at the given position, or the position is out of the block's
		bounds, then it indicates that the key is not in the dictionary.

		A tuple with two integer values is returned.  The first value
		is the block's index.  The second value is the position within
		the block in zero-based "pair" units.  E.g., position 3 indicates
		the fourth pair (indices 6 and 7 in the array).
		"""
		high, low = key >> self.BLOCKBITS, key % (1 << self.BLOCKBITS)
		if not high in self.__blocks:
			self.__blocks[high] = array.array('i')
		block = self.__blocks[high]
		n = len(block) // 2
		l, r = 0, n
		while l < r:
			m = l + (r - l) // 2
			t = block[2*m]
			if t == key:
				return high, m
			if t < key:
				l = m + 1
			else:
				r = m
		return high, l

	def __contains__(self, key):
		"""Tests whether a key is in the dictionary.  Examples:
		>>> d = IntIntDict({0: 0, 1: -1, 8: -2})
		>>> 0 in d
		True
		>>> -1 in d
		False
		"""
		b, p = self.__getpos(key)
		block = self.__blocks[b]
		n = len(block) // 2
		if p == n:
			return False
		return block[2*p] == key

	def __delitem__(self, key):
		"""Deletes a key from the dictionary.  Examples:
		>>> d = IntIntDict({0: 0, 1: -1, 8: -2})
		>>> 0 in d
		True
		>>> del d[0]
		>>> 0 in d
		False
		>>> del d[-1]
		Traceback (most recent call last):
			...
		KeyError: -1
		"""
		b, p = self.__getpos(key)
		block = self.__blocks[b]
		n = len(block) // 2
		if p == n or block[2*p] <> key:
			raise KeyError, key
		block.pop(2*p)
		block.pop(2*p)

	def __getitem__(self, key):
		"""Gets a value from the dictionary.  Examples:
		>>> d = IntIntDict({0: 0, 1: -1, 8: -2})
		>>> d[8]
		-2
		>>> del d[-1]
		Traceback (most recent call last):
			...
		KeyError: -1
		"""
		b, p = self.__getpos(key)
		block = self.__blocks[b]
		n = len(block) // 2
		if p == n:
			raise KeyError, key
		if block[2*p] == key:
			return block[2*p + 1]
		raise KeyError, key

	def __iter__(self):
		"""Iterates over the keys of the dictionary.  Examples:
		>>> d = IntIntDict({0: 0, 1: -1, 8: -2})
		>>> s = 0
		>>> for k in d: s += d[k]
		>>> s
		-3
		"""
		for b in self.__blocks:
			block = self.__blocks[b]
			n = len(block) // 2
			for p in xrange(n):
				yield block[2*p]

	def __len__(self):
		"""Returns the number of pairs in the dictionary.  Examples:
		>>> d = IntIntDict({0: 0, 1: -1, 8: -2})
		>>> len(d)
		3
		"""
		result = 0
		for b in self.__blocks:
			result += len(self.__blocks[b]) // 2
		return result

	def __repr__(self):
		"""Returns the "official" string representation of the dictionary."""
		return 'IntIntDict(' + str(self) + ')'

	def __setitem__(self, key, value):
		"""Adds a key-value pair to the dictionary.  Examples:
		>>> d = IntIntDict({0: 0, 1: -1, 8: -2})
		>>> -27 in d
		False
		>>> d[-27] = 3
		>>> -27 in d
		True
		>>> d[64] = 'Foo'
		Traceback (most recent call last):
			...
		TypeError: an integer is required
		"""
		b, p = self.__getpos(key)
		block = self.__blocks[b]
		n = len(block) // 2
		if p == n:
			block.append(key)
			block.append(value)
		elif block[2*p] == key:
			block[2*p + 1] = value
		else:
			block.insert(2*p, value)
			block.insert(2*p, key)

	def __str__(self):
		"""Returns an "informal" string representation of the dictionary."""
		result, count = '', 0
		for k in self:
			if count > 0:
				result += ', '
			if count == 100:
				result += '...'
				break
			result += str(k) + ': ' + str(self[k])
			count += 1
		return '{' + result + '}'

class CollisionError(Exception):
	pass

class HashIntDict:
	"""A dictionary-like structure with object hashes as keys
	and integers as values.

	During an attempt to reassign a key, the current key-value pair
	is removed and a collision flag for the key is set.  Subsequent
	attempts to access the key or check for its presence will either
	behave as if the key did not exist, or CollisionError will be
	raised, depending on the checking switch."""

	BLOCKBITS = 16

	def __init__(self, dictionary = {}, checking = False):
		"""Initializes the dictionary."""
		self.__checking = checking
		self.__collisions = IntSet()
		self.__dictionary = IntIntDict()
		for key in dictionary:
			self[key] = dictionary[key]

	def addcollision(self, key):
		self.__collisions.add(key)

	def removecollision(self, key):
		self.__collisions.remove(key)

	def getchecking(self):
		return self.__checking

	def setchecking(self, checking):
		self.__checking = bool(checking)

	def __contains__(self, key):
		key = hash(key)
		if self.__checking and key in self.__collisions:
			raise CollisionError
		return key in self.__dictionary

	def __delitem__(self, key):
		key = hash(key)
		if self.__checking and key in self.__collisions:
			raise CollisionError
		del self.__dictionary[key]

	def __getitem__(self, key):
		key = hash(key)
		if self.__checking and key in self.__collisions:
			raise CollisionError
		return self.__dictionary[key]

	def __iter__(self):
		for key in self.__dictionary:
			yield key

	def __len__(self):
		return len(self.__dictionary)

	def __repr__(self):
		return 'HashIntDict(' + str(self.__dictionary) + ', ' + str(self.__checking) + ')'

	def __setitem__(self, key, value):
		"""Attempts to add a key-value pair to the dictionary.

		If the key was already present in the dictionary,
		the current key-value pair is removed and a collision flag
		for the key is set.  Subsequent attempts to access the key
		or check for its presence will either behave as if the key
		did not exist, or CollisionError will be raised, depending
		on the checking switch.

		Examples for non-checking dictionary:
		>>> dn = HashIntDict({0: 0, 1: -1, 8: -2})
		>>> dn[8] = -2
		>>> 8 in dn
		True
		>>> dn[1] = 1
		>>> 1 in dn
		False

		Examples for checking dictionary:
		>>> dc = HashIntDict({0: 0, 1: -1, 8: -2}, True)
		>>> dc[8] = -2
		>>> 8 in dc
		True
		>>> dc[1] = 1
		>>> 1 in dc
		Traceback (most recent call last):
			...
		CollisionError
		"""
		key = hash(key)
		try:
			current = self.__dictionary[key]
			if current <> value:
				del self.__dictionary[key]
				self.__collisions.add(key)
		except KeyError:
			self.__dictionary[key] = value

	def __str__(self):
		return str(self.__dictionary)


if __name__ == '__main__':
	import doctest
	doctest.testmod()

