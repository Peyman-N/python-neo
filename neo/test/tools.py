from __future__ import with_statement
import numpy as np

import hashlib
import os
import quantities as pq

from neo import description

def assert_arrays_equal(a, b):
    assert isinstance(a, np.ndarray), "a is a %s" % type(a)
    assert isinstance(b, np.ndarray), "b is a %s" % type(b)
    assert a.shape == b.shape, "%s != %s" % (a,b)
    #assert a.dtype == b.dtype, "%s and %s not same dtype %s %s" % (a, b, a.dtype, b.dtype)
    assert (a.flatten()==b.flatten()).all(), "%s != %s" % (a, b)

def assert_arrays_almost_equal(a, b, threshold):
    assert isinstance(a, np.ndarray), "a is a %s" % type(a)
    assert isinstance(b, np.ndarray), "b is a %s" % type(b)
    assert a.shape == b.shape, "%s != %s" % (a,b)
    #assert a.dtype == b.dtype, "%s and %b not same dtype %s %s" % (a,b,a.dtype, b.dtype)
    if a.dtype.kind in ['f', 'c', 'i']:
        assert (abs(a - b) < threshold).all(), "max(|a - b|) = %s" % (abs(a - b)).max()

def file_digest(filename):
    with open(filename, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()

def assert_file_contents_equal(a, b):
    def generate_error_message(a, b):
        size_a = os.stat(a).st_size
        size_b = os.stat(b).st_size
        if size_a == size_b:
            return "Files have the same size but different contents"
        else:
            return "Files have different sizes: a:%d b: %d" % (size_a, size_b) 
                                 
    assert file_digest(a) == file_digest(b), generate_error_message(a, b)


def assert_neo_object_is_compliant(ob):
    """
    Test neo compliance of one object and sub objects (one_to_many_relation only):
      * check types and/or presence of necessary and recommended attribute.
      * If attribute is Quantities or numpy.ndarray it also check ndim.
      * If attribute is numpy.ndarray also check dtype.kind.
    """
    assert type(ob) in description.objectlist, '%s is not a neo object' % (type(ob))
    classname =ob.__class__.__name__
    necess = description.classes_necessary_attributes[classname]
    recomm = description.classes_recommended_attributes[classname]
    attributes = necess
    for i, attr in enumerate(attributes):
        attrname, attrtype = attr[0], attr[1]
        if attrname != '':
            assert hasattr(ob, attrname), '%s neo obect have not %s' %( classname, attrname)
    
    attributes = necess + recomm
    for i, attr in enumerate(attributes):
        attrname, attrtype = attr[0], attr[1]
        if attrname != '' and hasattr(ob, attrname):
            if getattr(ob, attrname) is not None:
                at = getattr(ob, attrname)
                assert type(at) == attrtype, '%s in %s have not the good type (%s should be %s)'%(attrname, classname, type(at), attrtype )
                if attrtype == pq.Quantity or attrtype == np.ndarray:
                    ndim = attr[2]
                    assert at.ndim == ndim,  '%s.%s  dimension is %d should be %d' % (classname, attrname, at.ndim, ndim)
                if attrtype == np.ndarray:
                    dt = attr[3]
                    assert at.dtype.kind == dt.kind, '%s.%s dtype.kind is %s should be %s' % (classname, attrname, at.dtype.kind, dt.kind)
                    
        elif attrname == '' and attrtype == pq.Quantity or attrtype == np.ndarray:
            ndim = attr[2]
            assert ob.ndim == ndim, '%s is %d dimension should be %d' %(classname, ob.ndim, ndim)
            if attrtype == np.ndarray:
                dt = attr[3]
                assert ob.dtype.kind == dt.kind, '%s dtype.kind is %s should be %s' % (classname, ob.dtype.kind, dt.kind)
            
    # recursive on one to many rel
    if classname in description.one_to_many_reslationship:
        for childname in description.one_to_many_reslationship[classname]:
            if not hasattr(ob, childname.lower()+'s'): continue
            sub = getattr(ob, childname.lower()+'s')
            for child in sub:
                assert_neo_object_is_compliant(child)




def assert_same_sub_schema(ob1, ob2, equal_almost = False, threshold = 1e-10):
    """
    Test if ob1 and ob2 has the same sub schema.
    Explore all one_to_many_relationship.
    Many_to_many_reslationship is not tested because of infinite recursive loops.
    
    Arguments:
        equal_almost: if False do a strict arrays_equal if True do arrays_almost_equal
    
    """
    assert type(ob1) == type(ob2), 'type(%s) != type(%s)' % (type(ob1), type(ob2))
    classname =ob1.__class__.__name__
    
    if classname in description.one_to_many_reslationship:
        # test one_to_many_relationship
        for child in description.one_to_many_reslationship[classname]:
            if not hasattr(ob1, child.lower()+'s'):
                assert not hasattr(ob2, child.lower()+'s'), '%s 2 do have %s but not %s 1'%(classname, child, classname)
                continue
            else:
                assert hasattr(ob2, child.lower()+'s'), '%s 1 have %s but not %s 2'%(classname, child, classname)
            
            sub1 = getattr(ob1, child.lower()+'s')
            sub2 = getattr(ob2, child.lower()+'s')
            assert len(sub1) == len(sub2), 'theses two %s have not the same %s number'%(classname, child)
            for i in range(len(getattr(ob1, child.lower()+'s'))):
                assert_same_sub_schema(sub1[i], sub2[i], equal_almost = equal_almost)
    
    # check if all attributes are equal
    if equal_almost:
        def assert_arrays_equal_and_dtype(a,b):
            assert_arrays_equal(a,b)
            assert a.dtype == b.dtype, "%s and %s not same dtype %s %s" % (a, b, a.dtype, b.dtype)
        assert_eg = assert_arrays_equal_and_dtype
    else:
        def assert_arrays_almost_and_dtype(a,b):
            assert_arrays_almost_equal(a,b,threshold)
            assert a.dtype == b.dtype, "%s and %s not same dtype %s %s" % (a, b, a.dtype, b.dtype)
        assert_eg = assert_arrays_almost_and_dtype
    
    necess = description.classes_necessary_attributes[classname]
    recomm = description.classes_recommended_attributes[classname]
    attributes = necess + recomm
    for i, attr in enumerate(attributes):
        attrname, attrtype = attr[0], attr[1]
        if not hasattr(ob1, attrname):
            assert not hasattr(ob2, attrname), '%s 2 do have %s but not %s 1'%(classname, attrname, classname)
            continue
        else:
            assert hasattr(ob2, attrname), '%s 1 have %s but not %s 2'%(classname, attrname, classname)
        
        if getattr(ob1,attrname)  is None:
            assert getattr(ob2,attrname)  is None, 'In %s.%s %s and %s differed' % (classname,attrname, getattr(ob1,attrname), getattr(ob2,attrname))
            continue
        if getattr(ob2,attrname)  is None:
            assert getattr(ob1,attrname)  is None, 'In %s.%s %s and %s differed' % (classname,attrname, getattr(ob1,attrname), getattr(ob2,attrname))
            continue
        
        if attrname =='': 
            # object is hinerited from Quantity (AnalogSIgnal, SpikeTrain, ...)
            assert_eg(ob1.magnitude, ob2.magnitude)
            assert ob1.dimensionality.string == ob2.dimensionality.string, 'Units of %s are not the same' % classname
        elif attrtype == pq.Quantity:
            assert_eg(ob1.__getattr__(attrname).magnitude, ob2.__getattr__(attrname).magnitude)
            assert ob1.__getattr__(attrname).dimensionality.string == ob2.__getattr__(attrname).dimensionality.string, 'Attribute %s of %s are not the same' % (attrname, classname)
        elif attrtype == np.ndarray:
            assert_eg(ob1.__getattr__(attrname), ob2.__getattr__(attrname))
        else:
            assert ob1.__getattr__(attrname) == ob2.__getattr__(attrname), 'Attribute %s.%s are not the same %s %s' % (classname,attrname, type(ob1.__getattr__(attrname)),  type(ob2.__getattr__(attrname)))

