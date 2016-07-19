""" tests basic functionality of DatabaseBuddy class """
import pytest
from collections import OrderedDict
import datetime
import random

from ... import buddy_resources as br
from ... import DatabaseBuddy as Db

# A few real accession numbers to test things out with
ACCNS = ["NP_001287575.1", "ADH10263.1", "XP_005165403.2", "A0A087WX72", "A0A096MTH0", "A0A0A9YFB0",
         "XM_003978475", "ENSAMEG00000011912", "ENSCJAG00000008732", "ENSMEUG00000000523"]


# ##################################################### GLOBALS ###################################################### #
def test_globals():
    assert Db.TRASH_SYNOS == ["t", "tb", "t_bin", "tbin", "trash", "trashbin", "trash-bin", "trash_bin"]
    assert Db.RECORD_SYNOS == ["r", "rec", "recs", "records", "main", "filtered"]
    assert Db.SEARCH_SYNOS == ["st", "search", "search-terms", "search_terms", "terms"]
    assert Db.DATABASES == ["ncbi_nuc", "ncbi_prot", "uniprot", "ensembl"]
    assert Db.RETRIEVAL_TYPES == ["protein", "nucleotide", "gi_num"]
    assert Db.FORMATS == ["ids", "accessions", "summary", "full-summary", "clustal", "embl", "fasta", "fastq",
                          "fastq-sanger", "fastq-solexa", "fastq-illumina", "genbank", "gb", "imgt", "nexus", "phd",
                          "phylip", "seqxml", "sff", "stockholm", "tab", "qual"]
    assert sorted(list(Db.CONFIG)) == ['data_dir', 'diagnostics', 'email', 'user_hash']
    assert type(Db.VERSION) == br.Version
    assert str(Db.VERSION) == """DatabaseBuddy 1.0 (%s)

Public Domain Notice
This is free software; see the source for detailed copying conditions.
There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.
Questions/comments/concerns can be directed to Steve Bond, steve.bond@nih.gov

Contributors:
Stephen Bond    https://github.com/biologyguy
Karl Keat       https://github.com/KarlKeat
Jeremy Labarge  https://github.com/biojerm
""" % datetime.date.today()
    assert Db.GREY == "\033[90m"
    assert Db.RED == "\033[91m"
    assert Db.GREEN == "\033[92m"
    assert Db.YELLOW == "\033[93m"
    assert Db.BLUE == "\033[94m"
    assert Db.MAGENTA == "\033[95m"
    assert Db.CYAN == "\033[96m"
    assert Db.WHITE == "\033[97m"
    assert Db.BOLD == "\033[1m"
    assert Db.UNDERLINE == "\033[4m"
    assert Db.NO_UNDERLINE == "\033[24m"
    assert Db.DEF_FONT == "\033[39m"


# ################################################# HELPER FUNCTIONS ################################################# #
def test_databaseerror():
    with pytest.raises(Db.DatabaseError) as err:
        raise Db.DatabaseError("Raised and err")
    assert "Raised and err" in str(err)


def test_stderr(capsys):
    Db._stderr("Hello from _stderr()")
    out, err = capsys.readouterr()
    assert err == "Hello from _stderr()"

    Db._stderr("Hello from _stderr()", quiet=True)
    out, err = capsys.readouterr()
    assert err == ""


def test_stdout(capsys):
    Db._stdout("Hello from _stdout()")
    out, err = capsys.readouterr()
    assert out == "Hello from _stdout()\033[m"

    Db._stdout("Hello from _stdout()", quiet=True)
    out, err = capsys.readouterr()
    assert out == ""

    Db._stdout("Hello from _stdout()", format_in=Db.RED)
    out, err = capsys.readouterr()
    assert out == "\x1b[91mHello from _stdout()\033[m"

    Db._stdout("Hello from _stdout()", format_in=[Db.UNDERLINE, Db.RED])
    out, err = capsys.readouterr()
    assert out == "\033[4m\x1b[91mHello from _stdout()\033[m"

    Db._stdout("Hello from _stdout()", format_out=Db.RED)
    out, err = capsys.readouterr()
    assert out == "Hello from _stdout()\x1b[91m"

    Db._stdout("Hello from _stdout()", format_out=[Db.UNDERLINE, Db.RED])
    out, err = capsys.readouterr()
    assert out == "Hello from _stdout()\033[4m\x1b[91m"

    with pytest.raises(AttributeError) as err:
        Db._stdout("Hello from _stdout()", format_in=["\033[4m", "\x1b[91"])
    assert "Malformed format_in attribute escape code" in str(err)

    with pytest.raises(AttributeError) as err:
        Db._stdout("Hello from _stdout()", format_out=["\033[4m", "\x1b[91"])
    assert "Malformed format_out attribute escape code" in str(err)


def test_terminal_colors():
    term_colors = Db.terminal_colors()
    for color in [Db.MAGENTA, Db.CYAN, Db.GREEN, Db.RED, Db.YELLOW, Db.GREY, Db.MAGENTA, Db.CYAN]:
        assert next(term_colors) == color


def test_check_database(capsys):
    assert Db.check_database() == Db.DATABASES
    assert Db.check_database('all') == Db.DATABASES
    assert Db.check_database('ALL') == Db.DATABASES
    assert Db.check_database('Foo') == Db.DATABASES
    out, err = capsys.readouterr()
    assert "Warning: 'foo' is not a valid database choice, omitted.\n" in err
    assert "Warning: No valid database choice provided. Setting to default 'all'.\n" in err
    assert Db.check_database("ncbi_prot") == ["ncbi_prot"]
    assert Db.check_database(["foo", "uniprot", "ncbi_prot"]) == ["uniprot", "ncbi_prot"]
    out, err = capsys.readouterr()
    assert "Warning: 'foo' is not a valid database choice, omitted.\n" in err


def test_check_type_protein():
    for _input in ["p", "pr", "prt", "prtn", "prn", "prot", "protn", "protien", "protein"]:
        assert Db.check_type(_input) == "protein"


def test_check_type_nuc():
    for _input in ["n", "ncl", "nuc", "dna", "nt", "gene", "transcript", "nucleotide"]:
        assert Db.check_type(_input) == "nucleotide"


def test_check_type_gi():
    for _input in ["g", "gi", "gn", "gin", "gi_num", "ginum", "gi_number"]:
        assert Db.check_type(_input) == "gi_num"


def test_check_type_default(capsys):
    assert not Db.check_type(None)
    assert Db.check_type("foo") == "protein"
    out, err = capsys.readouterr()
    assert err == "Warning: 'foo' is not a valid choice for '_type'. Setting to default 'protein'.\n"


# ################################################# SUPPORT CLASSES ################################################## #
def test_record_instantiation():
    with pytest.raises(TypeError) as err:
        Db.Record()
    assert "missing 1 required positional argument: '_accession'" in str(err)

    rec = Db.Record("Foo")
    assert rec.accession == "Foo"
    assert not rec.gi
    assert not rec.version
    assert not rec.record
    assert not rec.summary
    assert type(rec.summary) == OrderedDict
    assert not rec.size
    assert not rec.database
    assert not rec.type
    assert not rec.search_term
    assert str(rec) == "Accession:\tFoo\nDatabase:\tNone\nRecord:\tNone\nType:\tNone\n"

    rec = Db.Record("Foo", _size='5746')
    assert rec.size == 5746


def test_record_ncbi_accn():
    accns = ["NP_001287575.1", "ADH10263.1", "XP_005165403.2"]
    for accn in accns:
        rec = Db.Record(accn)
        assert not rec.version
        assert rec.ncbi_accn() == accn
        rec.guess_database()
        assert rec.ncbi_accn() == accn


def test_record_guess_refseq():
    ref_seq_nuc = ["NM_123456789", "NR_123456789", "XM_123456789", "XR_123456789"]
    for accn in ref_seq_nuc:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_nuc"
        assert rec.type == "nucleotide"

    ref_seq_chrom = ["NC_123456789", "XC_123456789"]
    for accn in ref_seq_chrom:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_nuc"
        assert rec.type == "nucleotide"

    ref_seq_prot = ["NM_123456789", "NR_123456789", "XM_123456789", "XR_123456789"]
    for accn in ref_seq_prot:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_nuc"
        assert rec.type == "nucleotide"


def test_record_guess_uniprot():
    randomly_generated_from_regex = ["K2O417", "I0DZU1", "A8GFV0", "J3K7W6", "O3U582", "C3YWY7GUS7", "Q0L5K7",
                                     "Q5FO16", "K9WMR5XBZ1"]
    for accn in randomly_generated_from_regex:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "uniprot"
        assert rec.type == "protein"


def test_record_guess_ensembl():
    accns = ["ENSRNOG00000018630", "ENSMUSG00000057666", "ENSPTRG00000004577",
             "ENSCAFG00000015077", "ENSPPYG00000004189", "ENSPCAG00000006928",
             "ENSOPRG00000012514", "ENSECAG00000022051", "ENSTSYG00000002171",
             "FBgn0001987", "FBtr0330306", "FBcl0254909"]
    for accn in accns:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ensembl"
        assert rec.type == "nucleotide"


def test_record_guess_genbank_nuc():
    randomly_generated_from_regex = ["PU844519", "I96398", "V72255", "M06308", "KP485089", "T79891", "R36898"]
    for accn in randomly_generated_from_regex:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_nuc"
        assert rec.type == "nucleotide"


def test_record_guess_genbank_prot():
    randomly_generated_from_regex = ["TXB10644", "DII59567", "FTJ23865", "SRR43454", "OIJ24077", "HNP42487", "TJS12387"]
    for accn in randomly_generated_from_regex:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_prot"
        assert rec.type == "protein"


def test_record_guess_genbank_pdb():
    randomly_generated_from_regex = ["2OOX", "4M7U", "700Y", "6TNH_2", "5CTC_C", "52O0", "3QNM"]
    for accn in randomly_generated_from_regex:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_prot"
        assert rec.type == "protein"


def test_record_guess_genbank_genome():
    randomly_generated_from_regex = ["LJIJ8045260586", "MRMV14919426", "WBGU8744627061", "WYNM11788712",
                                     "SQVS3339736221", "LVGB461502017", "FAWG101678469"]
    for accn in randomly_generated_from_regex:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_nuc"
        assert rec.type == "nucleotide"


def test_record_guess_genbank_mga():
    randomly_generated_from_regex = ["BJCKQ0111866", "YXRUT6401652", "PVAGD7038775", "OGSVS5937667",
                                     "LPMXX1503516", "NTEWQ3440974", "CTDME6774392"]
    for accn in randomly_generated_from_regex:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_prot"
        assert rec.type == "protein"


def test_record_guess_genbank_gi():
    randomly_generated_from_regex = ["13545654", "1445", "9876513546531", "154351", "135464316", "4684315", "021240"]
    for accn in randomly_generated_from_regex:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_nuc"
        assert rec.type == "gi_num"
        assert rec.gi == accn


def test_record_guess_genbank_version():
    accns = ["NP_001287575.1", "ADH10263.1", "XP_005165403.2"]
    for accn in accns:
        rec = Db.Record(accn)
        rec.guess_database()
        assert rec.database == "ncbi_prot"
        assert rec.type == "protein"
        accn, ver = accn.split(".")
        assert rec.accession == accn
        assert rec.version == ver


def test_record_search(sb_resources):
    summary = {"ACCN": "F6SBJ1", "DB": "uniprot", "entry_name": "F6SBJ1_HORSE", "length": "451",
               "organism-id": "9796", "organism": "Equus caballus (Horse)", "protein_names": "Caspase",
               "comments": "Caution (1); Sequence similarities (1)", "record": "summary"}
    rec = Db.Record("F6SBJ1", summary=summary)
    assert rec.search("*")
    assert not rec.search("Foo")

    # Length operator True
    assert rec.search("(length=451)")
    assert rec.search("(length >=451)")
    assert rec.search("(length<= 451)")
    assert rec.search("(length > 200)")
    assert rec.search("(length<500)")

    # Length operator False
    assert not rec.search("(length=452)")
    assert not rec.search("(length>=452)")
    assert not rec.search("(length<=450)")
    assert not rec.search("(length>500)")
    assert not rec.search("(length<200)")

    # Length operator errors
    with pytest.raises(ValueError) as err:
        rec.search("(length!<200)")
    assert "Invalid syntax for seaching 'length': length!<200" in str(err)

    with pytest.raises(ValueError) as err:
        rec.search("(length<>200)")
    assert "Invalid operator: <>" in str(err)

    # Other columns
    assert rec.search("(ACCN) [A-Z0-9]{6}")
    assert not rec.search("(ACCN) [A-Z0-9]{7}")
    assert rec.search("(comments)(Caution|Blahh)")
    assert not rec.search("(organism)Sheep")
    assert rec.search("(entry_name)")
    assert rec.search("(entry_name) ")
    assert not rec.search("(foo_name)")

    # No columns -> params
    assert rec.search("F6SBJ1")
    assert rec.search("uniprot")
    assert rec.search("protein")

    # No columns -> summary
    assert rec.search("Equus")
    assert not rec.search("equus")
    assert rec.search("i?equus")
    assert rec.search("?iEqUuS")

    # Genbank record
    sb_obj = sb_resources.get_one("p g")
    rec = Db.Record("Mle-Panxα8", _record=sb_obj.records[4])
    assert rec.search("Innexin")
    assert not rec.search("ML07312abcd")


def test_record_update():
    rec = Db.Record("K9WMR5XBZ1")
    summary = OrderedDict([("ACCN", "F6SBJ1"), ("DB", "uniprot"), ("entry_name", "F6SBJ1_HORSE"), ("length", "451"),
                           ("organism-id", "9796"), ("organism", "Equus caballus (Horse)"),
                           ("protein_names", "Caspase"), ("comments", "Caution (1); Sequence similarities (1)"),
                           ("record", "summary")])
    new_rec = Db.Record("F6SBJ1", gi=None, _version=None, _record=None, summary=summary, _size=451,
                        _database="uniprot", _type="protein", _search_term="casp9")
    rec.update(new_rec)
    assert rec.accession == "F6SBJ1"
    assert not rec.gi
    assert not rec.version
    assert not rec.record
    assert list(rec.summary) == ["ACCN", "DB", "entry_name", "length", "organism-id",
                                 "organism", "protein_names", "comments", "record"]
    assert rec.size == 451
    assert rec.database == "uniprot"
    assert rec.type == "protein"
    assert rec.search_term == "casp9"
    assert str(rec) == "Accession:\tF6SBJ1\nDatabase:\tuniprot\nRecord:\tNone\nType:\tprotein\n"


def test_failure_class():
    failure = Db.Failure("Q9JIJ4BYE", "Blahhh")
    assert failure.query == "Q9JIJ4BYE"
    assert failure.error_msg == "Blahhh"
    assert failure.hash == "26b3561cfa1e7047863784ece10867d4"
    assert str(failure) == "Q9JIJ4BYE\nBlahhh\n"


# ##################################################### DB BUDDY ##################################################### #
# Instantiation
def test_instantiate_empty_dbbuddy_obj():
    dbbuddy = Db.DbBuddy()
    assert dbbuddy.search_terms == []
    assert type(dbbuddy.records) == OrderedDict
    assert not dbbuddy.records
    assert dbbuddy.trash_bin == {}
    assert dbbuddy.out_format == "summary"
    assert dbbuddy.failures == {}
    assert dbbuddy.databases == ["ncbi_nuc", "ncbi_prot", "uniprot", "ensembl"]
    for client in ['ncbi', 'ensembl', 'uniprot']:
        assert dbbuddy.server_clients[client] == False
    assert dbbuddy.memory_footprint == 0


def test_instantiate_dbbuddy_from_path(sb_resources):
    tmp_file = br.TempFile()
    tmp_file.write(", ".join(ACCNS))
    dbbuddy = Db.DbBuddy(tmp_file.path)
    assert dbbuddy.search_terms == []
    for accn in ACCNS:
        assert accn in dbbuddy.records
    assert dbbuddy.trash_bin == {}
    assert dbbuddy.out_format == "summary"
    assert dbbuddy.failures == {}
    assert dbbuddy.databases == ["ncbi_nuc", "ncbi_prot", "uniprot", "ensembl"]
    for client in ['ncbi', 'ensembl', 'uniprot']:
        assert dbbuddy.server_clients[client] == False
    assert dbbuddy.memory_footprint == 0

    # Also test the other ways accessions can be in the file
    tmp_file.clear()
    split_chars = ["\t", "\n", "\r", " ", ","]
    tmp_file.write(ACCNS[0])
    for accn in ACCNS[1:]:
        tmp_file.write("%s%s" % (random.choice(split_chars), accn))
    dbbuddy = Db.DbBuddy(tmp_file.path)
    for accn in ACCNS:
        assert accn in dbbuddy.records


def test_instantiate_dbbuddy_from_handle():
    tmp_file = br.TempFile()
    tmp_file.write(", ".join(ACCNS))
    tmp_file.open("r")
    dbbuddy = Db.DbBuddy(tmp_file.handle)
    for accn in ACCNS:
        assert accn in dbbuddy.records


def test_instantiate_dbbuddy_from_plain_text():
    accns = ", ".join(ACCNS)
    dbbuddy = Db.DbBuddy(accns)
    for accn in ACCNS:
        assert accn in dbbuddy.records


def test_instantiate_dbbuddy_from_list():
    dbbuddy = Db.DbBuddy(", ".join(ACCNS))
    dbbuddy = Db.DbBuddy([dbbuddy, dbbuddy])
    for accn in ACCNS:
        assert accn in dbbuddy.records

    with pytest.raises(TypeError) as err:
        Db.DbBuddy(["foo", "bar"])
    assert "List of non-DbBuddy objects passed into DbBuddy as _input." in str(err)


def test_instantiate_dbbuddy_error():
    with pytest.raises(br.GuessError) as err:
        Db.DbBuddy({"Foo": "bar"})
    assert "DbBuddy could not determine the input type." in str(err)


def test_instantiate_dbbuddy_search_terms():
    dbbuddy = Db.DbBuddy("foobar, barfoo")
    assert dbbuddy.search_terms == ["foobar", "barfoo"]


# Methods

# ################################################# Database Clients ################################################# #
def test_uniprotrestclient_init():
    #client = Db.UniProtRestClient()
    pass