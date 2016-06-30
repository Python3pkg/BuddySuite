#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" tests basic functionality of AlignBuddy class """
import pytest
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.AlignIO import MultipleSeqAlignment
from Bio.Alphabet import IUPAC
try:
    from buddysuite import AlignBuddy as Alb
    from buddysuite import SeqBuddy as Sb
    from buddysuite import buddy_resources as br
except ImportError:
    import AlignBuddy as Alb
    import SeqBuddy as Sb
    import buddy_resources as br


TEMPDIR = br.TempDir()


# ##########################################  '-al', '--alignment_lengths' ########################################### #
def test_alignment_lengths(alb_resources):
    lengths = Alb.alignment_lengths(alb_resources.get_one("m p c"))
    assert lengths[0] == 481
    assert lengths[1] == 683

    lengths = Alb.alignment_lengths(alb_resources.get_one("m d s"))
    assert lengths[0] == 2043
    assert lengths[1] == 1440


# ##############################################  '-bts', '--bootstrap' ############################################## #
def test_bootstrap(alb_resources, alb_helpers):
    # Test an amino acid file
    tester = Alb.bootstrap(alb_resources.get_one("m p py"))
    assert tester.lengths() == [681, 480]

    tester = Alb.bootstrap(alb_resources.get_one("m p py"), 3)
    assert tester.lengths() == [681, 681, 681, 480, 480, 480]

    # Also get a really short alignment, and make sure all the expected columns are showing up
    tester = Alb.extract_regions(alb_resources.get_one("o d n"), 13, 15)
    _hashes = ["19157b79a55467e22e503d7da0f48862", "dd16e900e9c885224b65a97cb382df3b",
               "9c2f83134a03dec93ca51ce22960779d", "02d6ada0beaf429e73a5f1b29ac00fff"]
    for _ in range(20):
        assert alb_helpers.align_to_hash(Alb.bootstrap(tester)) in _hashes


# ##############################################  '-cs', '--clean_seqs' ############################################## #
def test_clean_seqs(alb_resources, alb_helpers):
    # Test an amino acid file
    tester = Alb.clean_seq(alb_resources.get_one("m p py"))
    assert alb_helpers.align_to_hash(tester) == "07a861a1c80753e7f89f092602271072"

    tester = Alb.clean_seq(Alb.AlignBuddy("%s/ambiguous_dna_alignment.fa" % alb_helpers.resource_path),
                           ambiguous=False, rep_char="X")
    assert alb_helpers.align_to_hash(tester) == "6755ea1408eddd0e5f267349c287d989"


# ###########################################  '-cta', '--concat_alignments' ######################################### #
def test_concat_alignments(alb_resources, alb_helpers):
    with pytest.raises(AttributeError) as e:
        Alb.concat_alignments(alb_resources.get_one("p o g"), '.*')
    assert "Please provide at least two alignments." in str(e)

    tester = alb_resources.get_one("o p g")
    tester.alignments.append(alb_resources.get_one("o p g").alignments[0])

    with pytest.raises(ValueError) as e:
        Alb.concat_alignments(tester, 'foo')
    assert "No match found for record" in str(e)

    with pytest.raises(ValueError) as e:
        Alb.concat_alignments(tester, 'Panx')
    assert "Replicate matches" in str(e)

    tester = Sb.SeqBuddy("%s/Cnidaria_pep.nexus" % alb_helpers.resource_path)
    Sb.pull_recs(tester, "Ccr|Cla|Hec")
    tester = Alb.AlignBuddy(str(tester))
    tester.alignments.append(tester.alignments[0])
    assert alb_helpers.align_to_hash(Alb.concat_alignments(Alb.make_copy(tester))) == '32a507107b7dcd044ea7760c8812441c'

    tester.set_format("gb")
    tester2 = Alb.concat_alignments(Alb.make_copy(tester), "(.).(.)-Panx(.)")
    assert alb_helpers.align_to_hash(tester2) == '5ac908ebf7918a45664a31da480fda58'

    tester.set_format("gb")
    tester2 = Alb.concat_alignments(Alb.make_copy(tester), "(.).(.)-Panx(.)")
    assert alb_helpers.align_to_hash(tester2) == '5ac908ebf7918a45664a31da480fda58'

    tester.set_format("gb")
    tester2 = Alb.concat_alignments(Alb.make_copy(tester), "...", "Panx.*")
    assert alb_helpers.align_to_hash(tester2) == 'e754350b0397cf54f531421d1e85774f'

    tester.set_format("gb")
    tester2 = Alb.concat_alignments(Alb.make_copy(tester), "...", "(P)an(x)(.)")
    assert alb_helpers.align_to_hash(tester2) == '5c6653aec09489cadcbed68fbd2f7465'

    shorten = Alb.delete_records(Alb.make_copy(tester), "Ccr")
    tester.alignments[1] = shorten.alignments[1]
    assert alb_helpers.align_to_hash(Alb.concat_alignments(Alb.make_copy(tester))) == 'f3ed9139ab6f97042a244d3f791228b6'


# ###########################################  '-con', '--consensus' ############################################ #
hashes = [('o d g', '888a13e13666afb4d3d851ca9150b442'), ('o d n', '560d4fc4be7af5d09eb57a9c78dcbccf'),
          ('o d py', '01f1181187ffdba4fb08f4011a962642'), ('o d s', '51b5cf4bb7d591c9d04c7f6b6bd70692'),
          ('o r n', '1123b95374085b5bcd079880b7762801'), ('o p g', '2c038a306713800301b6b4cdbcf61659'),
          ('o p n', '756a3334c70f9272e2d9cb74dba9ad52'), ('o p py', 'aaf1d5aff561c1769dd267ada2fea8b0'),
          ('o p s', 'b6f72510eeef6be0752ae86d72a44283'), ('m d py', '0ae422fa0fafbe0f2edab9a042fb7834'),
          ('m d s', '7b0aa3cca159b276158cf98209be7dab'), ('m p py', '460033d892db36d4750bafc6998d42d0'),
          ('m p s', '89130797253646e61b78ab7d91ad3fd9')]


@pytest.mark.parametrize("key,next_hash", hashes)
def test_consensus(alb_resources, alb_helpers, key, next_hash):
    tester = Alb.consensus_sequence(alb_resources.get_one(key))
    assert alb_helpers.align_to_hash(tester) == next_hash, tester.write("error_files/%s" % next_hash)


# ###########################################  '-dr', '--delete_records' ############################################ #
hashes = [('o d g', 'b418ba198da2b4a268a962db32cc2a31'), ('o d n', '355a98dad5cf382797eb907e83940978'),
          ('o d py', 'fe9a2776558f3fe9a1732c777c4bc9ac'), ('o d s', '35dc92c4f4697fb508eb1feca43d9d75'),
          ('o r n', '96e6964115200d46c7cb4eb975718304'), ('o p g', '50e09d37a92af595f6fe881d4e57bfc5'),
          ('o p n', '1cfaa4109c5db8fbfeaedabdc57af655'), ('o p py', '1d0e7b4d8e89b42b0ef7cc8c40ed1a93'),
          ('o p s', '1578d98739d2aa6196463957c7b408fa'), ('m d py', 'db4ed247b40707e8e1f0622bb420733b'),
          ('m d s', 'de5beddbc7f0a7f8e3dc2d5fd43b7b29'), ('m p py', '31f91f7dc548e4b075bfb0fdd7d5c82c'),
          ('m p s', '043e35023b355ed560166db9130cfe30')]


@pytest.mark.parametrize("key,next_hash", hashes)
def test_delete_records(alb_resources, alb_helpers, key, next_hash):
    tester = Alb.delete_records(alb_resources.get_one(key), "α[1-5]|β[A-M]")
    assert alb_helpers.align_to_hash(tester) == next_hash, tester.write("error_files/%s" % next_hash)


# ######################  'd2r', '--transcribe' and 'r2d', '--reverse_transcribe' ###################### #
hashes = [('o d g', '4bf291d91d4b27923ef07c660b011c72', '2a42c56df314609d042bdbfa742871a3'),
          ('o d n', 'e531dc31f24192f90aa1f4b6195185b0', 'cb1169c2dd357771a97a02ae2160935d'),
          ('o d py', 'e55bd18b6d82a7fc3150338173e57e6a', '503e23720beea201f8fadf5dabda75e4'),
          ('o d s', '45b511f34653e3b984e412182edee3ca', '228e36a30e8433e4ee2cd78c3290fa6b'),
          ('m d py', '16cb082f5cd9f103292ccea0c4d65a06', '42679a32ebd93b628303865f68b0293d'),
          ('m d s', 'd81dae9714a553bddbf38084f7a8e00e', 'ae352b908be94738d6d9cd54770e5b5d')]


@pytest.mark.parametrize("key,d2r_hash,r2d_hash", hashes)
def test_transcribe(alb_resources, alb_helpers, key, d2r_hash, r2d_hash):
    tester = Alb.dna2rna(alb_resources.get_one(key))
    assert alb_helpers.align_to_hash(tester) == d2r_hash, tester.write("error_files/%s" % d2r_hash)
    tester = Alb.rna2dna(tester)
    assert alb_helpers.align_to_hash(tester) == r2d_hash, tester.write("error_files/%s" % r2d_hash)


def test_transcribe_exceptions(alb_resources):
    with pytest.raises(TypeError) as e:
        Alb.dna2rna(alb_resources.get_one("o p s"))
    assert "TypeError: DNA sequence required, not IUPACProtein()." in str(e)

    with pytest.raises(TypeError) as e:
        Alb.dna2rna(alb_resources.get_one("o r n"))
    assert "TypeError: DNA sequence required, not IUPACAmbiguousRNA()." in str(e)


def test_reverse_transcribe_exceptions(alb_resources):  # Asserts that a TypeError will be thrown if user inputs protein
    with pytest.raises(TypeError) as e:
        Alb.rna2dna(alb_resources.get_one("o p s"))
    assert "TypeError: RNA sequence required, not IUPACProtein()." in str(e)

    with pytest.raises(TypeError) as e:
        Alb.rna2dna(alb_resources.get_one("o d s"))
    assert "TypeError: RNA sequence required, not IUPACAmbiguousDNA()." in str(e)


# ###########################################  '-et', '--enforce_triplets' ########################################### #
hashes = [('o d g', '6ff2a8a7c58bb6ac0d98fe373981e220'), ('o d n', 'c907d29434fe2b45db60f1a9b70f110d'),
          ('o d py', 'b6cf61c86588023b58257c9008c862b5'), ('o r n', '0ed7383ab2897f8350c2791739f0b0a4'),
          ('m d py', '669ffc4fa602fb101c559cb576bddee1')]


@pytest.mark.parametrize("key,next_hash", hashes)
def test_enforce_triplets(key, next_hash, alb_resources, alb_helpers):
    tester = Alb.enforce_triplets(alb_resources.get_one(key))
    assert alb_helpers.align_to_hash(tester) == next_hash, tester.write("error_files/%s" % next_hash)


def test_enforce_triplets_error(alb_resources):
    with pytest.raises(TypeError) as e:
        Alb.enforce_triplets(alb_resources.get_one("m p c"))
    assert "Nucleic acid sequence required, not protein." in str(e)

    with pytest.raises(TypeError) as e:
        tester = Alb.enforce_triplets(alb_resources.get_one("m d pr"))
        tester.alignments[0][0].seq = Seq("MLDILSKFKGVTPFKGITIDDGWDQLNRSFMFVLLVVMGTTVTVRQYTGSVISCDGFKKFGSTFAEDYCWTQGLY",
                                          alphabet=IUPAC.protein)
        Alb.enforce_triplets(tester)
    assert "Record 'Mle-Panxα9' is protein. Nucleic acid sequence required." in str(e)

# ###########################################  'er', '--extract_regions' ############################################ #
hashes = [('o d g', 'aaa69d3abb32876a2774d981a274cbad'), ('o d n', '10ca718b74f3b137c083a766cb737f31'),
          ('o d py', 'd738a9ab3ab200a7e013177e1042e86c'), ('o p g', '836ca0e0d42da0679b9dc8fe4a6e390a'),
          ('o p n', '5f400edc6f0990c0cd6eb52ae7687e39'), ('o p py', '69c9ad73ae02525150d4682f9dd68093'),
          ('m d py', 'd06ba679c8a686c8f077bb460a4193b0'), ('m p py', '8151eeda36b9a170512709829d70230b')]


@pytest.mark.parametrize("key,next_hash", hashes)
def test_extract_range(key, next_hash, alb_resources, alb_helpers):
    tester = Alb.extract_regions(alb_resources.get_one(key), 0, 50)
    assert alb_helpers.align_to_hash(tester) == next_hash, tester.write("error_files/%s" % next_hash)


# ###########################################  'ga', '--generate_alignment' ########################################## #
# ToDo: All of these tests need to be run on mock output. Actual 3rd party software is tested in test_alb_3rd_party.py

def test_pagan(alb_resources, alb_helpers):
    pass


def test_prank():
    pass


def test_muscle():
    pass


def test_clustalw2():
    pass


def test_clustalomega():
    pass


def test_mafft():
    pass


def test_generate_alignment_keep_temp(monkeypatch):
    pass


# ######################  '-hi', '--hash_ids' ###################### #
def test_hash_seq_ids(alb_resources):
    tester = alb_resources.get_one("o p g")
    Alb.hash_ids(tester)
    assert len(tester.records()[0].id) == 10

    tester = alb_resources.get_one("m d pr")
    Alb.hash_ids(tester, 25)
    assert len(tester.records()[0].id) == 25
    assert len(tester.hash_map) == 34


def test_hash_seq_ids_errors(alb_resources):
    tester = alb_resources.get_one("o d f")

    with pytest.raises(TypeError) as e:
        Alb.hash_ids(tester, "foo")
    assert str(e.value) == "Hash length argument must be an integer, not <class 'str'>"

    with pytest.raises(ValueError) as e:
        Alb.hash_ids(tester, 0)
    assert str(e.value) == "Hash length must be greater than 0"

    tester.alignments *= 10
    with pytest.raises(ValueError) as e:
        Alb.hash_ids(tester, 1)
    assert "Insufficient number of hashes available to cover all sequences." in str(e.value)


# #################################### 'lc', '--lowercase' and 'uc', '--uppercase' ################################### #
hashes = [('o d g', '2a42c56df314609d042bdbfa742871a3', '2a42c56df314609d042bdbfa742871a3'),
          ('o d n', '52e74a09c305d031fc5263d1751e265d', 'cb1169c2dd357771a97a02ae2160935d'),
          ('o d py', 'cfe6cb9c80aebd353cf0378a6d284239', '503e23720beea201f8fadf5dabda75e4'),
          ('o d s', 'b82538a4630810c004dc8a4c2d5165ce', '228e36a30e8433e4ee2cd78c3290fa6b'),
          ('o p g', 'bf8485cbd30ff8986c2f50b677da4332', 'bf8485cbd30ff8986c2f50b677da4332'),
          ('o p n', '8b6737fe33058121fd99d2deee2f9a76', '17ff1b919cac899c5f918ce8d71904f6'),
          ('o p py', '968ed9fa772e65750f201000d7da670f', 'aacda2f5d4077f23926400f74afa2f46'),
          ('o p s', 'f35cbc6e929c51481e4ec31e95671638', 'c0dce60745515b31a27de1f919083fe9'),
          ('m d py', '6259e675def07bd4977f4ab1f5ffc26d', '0974ac9aefb2fb540957f15c4869c242'),
          ('m d s', 'f3f7b66ef034d3807683a2d5a0c44cad', 'a217b9f6000f9eeff98faeb9fd09efe4'),
          ('m p py', '2a77f5761d4f51b88cb86b079e564e3b', 'd13551548c9c1e966d0519755a8fb4eb'),
          ('m p s', '6f3f234d796520c521cb85c66a3e239a', '00661f7afb419c6bb8c9ac654af7c976')]


@pytest.mark.parametrize("key,uc_hash,lc_hash", hashes)
def test_cases(key, uc_hash, lc_hash, alb_resources, alb_helpers):
    tester = Alb.uppercase(alb_resources.get_one(key))
    assert alb_helpers.align_to_hash(tester) == uc_hash, tester.write("error_files/%s" % uc_hash)
    tester = Alb.lowercase(tester)
    assert alb_helpers.align_to_hash(tester) == lc_hash, tester.write("error_files/%s" % lc_hash)


# ##################### '-mf2a', '--map_features2alignment' ###################### ##
hashes = [('o p n', '79078260e8725a0d7ccbed9400c78eae'), ('o p pr', '02b977e5b086125255b792788014708a'),
          ('o p psr', '02b977e5b086125255b792788014708a'), ('o p s', '372daf72435e2f1a06531b5c030995c6'),
          ('o d n', '9fece109249f4d787c13e6fb2742843d'), ('o d pr', '899c6ab534f7af07e744eb173e94bd50'),
          ('o d psr', '899c6ab534f7af07e744eb173e94bd50'), ('o d s', '79cf44688165842eba1bb45b3543d458')]


@pytest.mark.parametrize("key,next_hash", hashes)
def test_map_features2alignment(key, next_hash, alb_resources, alb_helpers):
    alignbuddy = alb_resources.get_one(key)
    if alignbuddy.alpha == IUPAC.protein:
        seqbuddy = Sb.SeqBuddy("%s/Mnemiopsis_pep.gb" % alb_helpers.resource_path)
    else:
        seqbuddy = Sb.SeqBuddy("%s/Mnemiopsis_cds.gb" % alb_helpers.resource_path)
    tester = Alb.map_features2alignment(seqbuddy, alignbuddy)
    tester.set_format("genbank")
    assert alb_helpers.align_to_hash(tester) == next_hash, tester.write("error_files/%s" % next_hash)


# ###########################################  '-oi', '--order_ids' ############################################ #
hashes = [('o d g', '37df4bfa14878fc2772710da243942b6', '7dc190f41c9fb1f96956abd579a00282'),
          ('o d n', '132757da01b3caf174d024efdb2c3acd', '286bac7a213997924203622c3357457c'),
          ('o d py', '3c49bdc1b0fe4e1d6bfc148eb0293e21', 'd6e79a5faeaff396aa7eab0b460c3eb9'),
          ('o p g', '5b1f35e89b7e93039948e27482bdf305', 'cecaa08ef55b850345ece0bc12fbf5b7'),
          ('o p n', '197ba12e799ab2a1dadfe1b254381e00', 'f32fabc627615d25d8cd57553e7281af'),
          ('o p py', 'ffae954adc0d362354e43c1b70d9be29', 'f4c0924087fdb624823d02e909d94e95'),
          ('m d py', 'a44938e26e4b35967ed8e17a0eaebe4c', '9d6b6087d07f7d1fd701591ab7cb576d'),
          ('m p py', '5bdda310b29b18057e056f3c982446b2', '439f57b891dd2a72724b10c124f96378')]


@pytest.mark.parametrize("key,fwd_hash,rev_hash", hashes)
def test_order_ids1(key, fwd_hash, rev_hash, alb_resources, alb_helpers):
    alignbuddy = alb_resources.get_one(key)
    Alb.order_ids(alignbuddy)
    assert alb_helpers.align_to_hash(alignbuddy) == fwd_hash, alignbuddy.write("error_files/%s" % fwd_hash)

    Alb.order_ids(alignbuddy, reverse=True)
    assert alb_helpers.align_to_hash(alignbuddy) == rev_hash, alignbuddy.write("error_files/%s" % rev_hash)


def test_order_ids2(alb_resources, alb_helpers):
    alignbuddy = alb_resources.get_one("o p n")
    Alb.rename(alignbuddy, "Mle-Panxα4", "Mle004-Panxα4")
    Alb.rename(alignbuddy, "Mle-Panxα5", "Mle05-Panxα5")
    Alb.rename(alignbuddy, "Mle-Panxα9", "aMle-PanxαBlahh")
    Alb.order_ids(alignbuddy)
    assert alb_helpers.align_to_hash(alignbuddy) == "5c1316e18205432b044101e720646cd5"

# ##################### '-pr', '--pull_records' ###################### ##
hashes = [('o d g', '7d1091e16adc09e658563867e7c6bc35'), ('o d n', 'd82e66c57548bcf8cba202b13b070ead'),
          ('o d py', 'd141752c38a892ccca800c637f609608'), ('o p g', 'efe1f01a6372519e314003572a269702'),
          ('o p n', '027bbc7e34522f9521f83ee7d03793a1'), ('o p py', '2cd74d7ede4d1fb6e18363567426437e'),
          ('m d py', '7c77c6f3245c21842f4be585714ec6ce'), ('m p py', 'f34fa4c34cfe5c1e6b228949557c9483')]


@pytest.mark.parametrize("key,next_hash", hashes)
def test_pull_records(key, next_hash, alb_resources, alb_helpers):
    alignbuddy = alb_resources.get_one(key)
    Alb.pull_records(alignbuddy, "α[1-5]$|β[A-M]")
    assert alb_helpers.align_to_hash(alignbuddy) == next_hash, alignbuddy.write("error_files/%s" % next_hash)


# ###########################################  '-ri', '--rename_ids' ############################################ #
hashes = [('o d g', 'c35db8b8353ef2fb468b0981bd960a38'), ('o d n', '243024bfd2f686e6a6e0ef65aa963494'),
          ('o d py', '98bb9b57f97555d863054ddb526055b4'), ('o p g', '2e4e3c365cd011821bcdc6275a3559af'),
          ('o p n', '3598e85169ed3bcdbcb676bb2eb6cef0'), ('o p py', 'd49eb4de01d727b9e3ad648d6a04a3c9'),
          ('m d py', 'ddfffd9b999637abf7f5926f017de987'), ('m p py', '0a68229bd13439040f045cd8c72d7cc9')]


@pytest.mark.parametrize("key,next_hash", hashes)
def test_rename_ids(key, next_hash, alb_resources, alb_helpers):
    alignbuddy = alb_resources.get_one(key)
    Alb.rename(alignbuddy, 'Panx', 'Test', 0)
    assert alb_helpers.align_to_hash(alignbuddy) == next_hash, alignbuddy.write("error_files/%s" % next_hash)


# ###########################################  'tr', '--translate' ############################################ #
hashes = [('o d f', 'b7fe22a87fb78ce747d80e1d73e39c35'), ('o d g', 'a949edce98525924dbbc3ced03c18214'),
          ('o d n', 'a2586af672ad71f16bbd54f359b323ff'), ('o d py', 'd0d4dd408e559215b2780f4f0ae0c418'),
          ('o d pr', 'f77705e32cd753267916539ee0936e1f'), ('o d pss', 'ede672b15221ec60981287ca1e286c52'),
          ('o d psr', '623fe1634752e812f482cfa7b7ea20ee'), ('o d s', '4ff563c39229d30aa3eda193cb290344'),
          ('o d c', '150179326629fffadb7aef7796bd1cec'), ('m d py', '7fd28236f491c38ba261dfde20919595'),
          ('m d pr', '0de676236eda864172b73b6abe4d7a05'), ('m d pss', 'c7feff60c16b2b187e03db5d160a4748'),
          ('m d psr', 'b5945f0317fe9ce8fc03ac7f4c0d5932'), ('m d s', 'ee5a41b6f8b32645359beafc72efe825'),
          ('m d c', '09251e1f4fc0e07a5bba4c64c22bac9b')]


@pytest.mark.parametrize("key,next_hash", hashes)
def test_translate1(key, next_hash, alb_resources, alb_helpers):
    alignbuddy = alb_resources.get_one(key)
    Alb.translate_cds(alignbuddy)
    assert alb_helpers.align_to_hash(alignbuddy) == next_hash, alignbuddy.write("error_files/%s" % next_hash)


def test_translate2(alb_resources):
    # Protein input
    with pytest.raises(TypeError) as e:
        Alb.translate_cds(alb_resources.get_one('o p s'))
    assert "Nucleic acid sequence required, not protein." in str(e)

    tester = alb_resources.get_one('o d s')
    tester.records()[0].seq.alphabet = IUPAC.protein
    with pytest.raises(TypeError) as e:
        Alb.translate_cds(tester)
    assert "Record 'Mle-Panxα9' is protein." in str(e)

# ###########################################  'tm', '--trimal' ############################################ #
hashes = [('o d psr', '5df948e4b2cb6c0d0740984445655135', '384563eb411713e90cb2fea0c799bf0d'),
          ('m d psr', '0e93f0a8c77da8ec974eeca311ca6636', 'b15f333416e9dd44834f468d5cd4ca8d'),
          ('o p psr', 'b87f927511aade73bc795e024af8975e', 'e0f5ce9201249daf4bb3b4f70a7b5ce8'),
          ('m p psr', 'f0f2115e29f6dfcb75036d90b06edab4', 'f443fbe1831fe368a11edc51e25fa330')]


@pytest.mark.parametrize("key,hash3,hash07", hashes)
def test_trimal(key, hash3, hash07, alb_resources, alb_helpers):
    alignbuddy = alb_resources.get_one(key)
    tester1, tester2 = Alb.make_copy(alignbuddy), Alb.make_copy(alignbuddy)
    Alb.trimal(tester1, 3)
    assert alb_helpers.align_to_hash(tester1) == hash3, alignbuddy.write("error_files/%s" % hash3)

    tester1, tester2 = Alb.make_copy(alignbuddy), Alb.make_copy(alignbuddy)
    Alb.trimal(tester1, 0.7)
    assert alb_helpers.align_to_hash(tester1) == hash07, alignbuddy.write("error_files/%s" % hash07)


def test_trimal2(alb_resources, alb_helpers):
    tester = Alb.trimal(alb_resources.get_one("o p n"), 'all')
    assert alb_helpers.align_to_hash(tester) == "8faaf09741ddb3137653cb77ee66974a"
    tester = alb_resources.get_one("o p n")
    tester.alignments[0]._records = tester.alignments[0]._records[:5]
    Alb.trimal(tester, 'clean')
    assert alb_helpers.align_to_hash(tester) == "93a2aa21e6baf5ca70eb2de52ae8dbea"
    tester = alb_resources.get_one("o p n")
    tester_dir = TEMPDIR.subdir()
    tester.write("%s/trimal" % tester_dir)
    assert alb_helpers.align_to_hash(Alb.trimal(tester, 'gappyout')) == "2877ecfb201fc35211a4625f34c7afdd"
    """ Probably not a good idea to be calling binaries like this...
    real_trimal = Popen("trimal -in %s/trimal -gappyout" % tester_dir, stdout=PIPE, shell=True).communicate()
    real_trimal = real_trimal[0].decode()
    with open("%s/trimal" % tester_dir, "w") as ofile:
        ofile.write(real_trimal)
    tester = Alb.AlignBuddy("%s/trimal" % tester_dir)
    assert alb_helpers.align_to_hash(tester) == "2877ecfb201fc35211a4625f34c7afdd"
    """
    records = [SeqRecord(Seq("A--G-")), SeqRecord(Seq("--T--")), SeqRecord(Seq("--TG-")), SeqRecord(Seq("A---C"))]
    tester = Alb.AlignBuddy([MultipleSeqAlignment(records)])
    Alb.trimal(tester, "gappyout")
    assert "".join([str(rec.seq) for rec in tester.records()]) == ""