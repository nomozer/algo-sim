import sys; sys.path.insert(0, ".")
sys.argv=[sys.argv[0], sys.argv[1]]
exec(open(sys.argv[0].replace("probe2.py","probe.py"),encoding="utf-8").read().split("for t in AUX:")[0])
for t,q in [("Tính bình phương khoảng cách từ S đến BD.","Tính bìnhphương khoảng cách từ S đến BD."),
            ("Tính nửa khoảng cách từ S đến BD.","Tính nửakhoảng cách từ S đến BD."),
            ("Tính bình phương khoảng cách từ S đến BD.","bìnhphươngkhoảng cách từ S đến BD."),
            ("Tính bình phương khoảng cách từ S đến BD.","Tính bình phươngkhoảng cách từ S đến BD.")]:
    print("AUXWS", repr(q), aux(t,q))
for t,q in [('Tính bình phương khoảng cách từ M đến giao tuyến của (SAC) và (SBD).','bìnhphươngkhoảng cách từ M đến giao tuyến của (SAC) và (SBD).'),
            ('Tính nửa khoảng cách từ M đến giao tuyến của (SAC) và (SBD).','Tính nửakhoảng cách từ M đến giao tuyến của (SAC) và (SBD).')]:
    print("LREFWS", repr(q), lref(t,q))
