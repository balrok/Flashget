# Imeem.com Python Crypto API
# devloop.lyua.org - 03/2009

# un byte : entier sur 8 bits
# un char : caractere sur 8 bits
# un block : 4 bytes

class Crypt:

  a2b = {}
  b2a = {}

  def __init__(self, log):
    self.log = log
    i = 0
    # Chaine de 64 caracteres utilises pour les codages ASCII
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_":
      self.a2b[c] = i
      i += 1
    for k, v in self.a2b.items():
      self.b2a[v] = k

  def str2bytes(self, s):
    t = []
    for c in s:
      t.append(ord(c))
    return t

  def blocks2bytes(self, blocks):
    bytes = {}
    for i in xrange(0, len(blocks)):
      iby = i * 4
      bytes[iby + 0] = 255 & blocks[i] >> 24
      bytes[iby + 1] = 255 & blocks[i] >> 16
      bytes[iby + 2] = 255 & blocks[i] >> 8
      bytes[iby + 3] = 255 & blocks[i]
    return bytes

  def bytes2blocks(self, bytes):
    # retour un tableau de long (sur 8 octets)
    blocks = {}
    iby = 0
    ibl = 0
    while True:
      blocks[ibl] = (255 & bytes[iby]) << 24
      iby += 1
      if iby >= len(bytes):
        break
      blocks[ibl] |= (255 & bytes[iby]) << 16
      iby += 1
      if iby >= len(bytes):
        break
      blocks[ibl] |= (255 & bytes[iby]) << 8
      iby += 1
      if iby >= len(bytes):
        break
      blocks[ibl] |= (255 & bytes[iby])
      iby += 1
      if iby >= len(bytes):
        break
      ibl += 1
    return blocks

  def binary2str(self, bks):
    return self.bytes2str(self.blocks2bytes(bks))

  def pad(self,bytearray):
    newarray    = {}
    npads       = 7 - (len(bytearray) % 8)
    newarray[0] = npads
    blen = len(bytearray)
    for i in xrange(0, blen):
      newarray[i + 1] = bytearray[i]
    for i in xrange(0, npads):
      newarray[i + blen + 1] = 0
    return newarray

  def bytes2ascii(self, b):
    s = ""
    ib = 0
    b1 = 0
    b2 = 0
    b3 = 0
    carry = 0

    # on prend 3 octets (soit 24 bits) que l'on decoupe en 4 blocks de 6 bits
    # soit 64 valeurs possibles qui servent comme index pour un caractere ASCII
    blen = len(b)
    while True:
      if ib >= blen:
        break
      b1 = 255 & b[ib]
      # 63 = masque 0x3F - elimine les deux premiers bits (poids fort)
      s += self.b2a[63 & b1 >> 2]
      # carry prend les deux derniers bits (poids faible)
      carry = 3 & b1
      ib += 1
      if ib >= blen:
        s += self.b2a[carry << 4]
        break
      b2 = 255 & b[ib]
      # 240 = masque 0xF0 - elimine les quatres derniers bits
      s += self.b2a[240 & carry << 4 | b2 >> 4]
      # carry prend les quatres derniers bits (poids faible)
      carry = 15 & b2
      ib += 1
      if ib >= blen:
        s += self.b2a[carry << 2]
        break
      b3 = 255 & b[ib]
      # 60 = masque 0x3C - elimine les deux premiers et deux derniers bits
      # 63 = masque 0x3F - elimine les deux premiers bits (poids fort)
      s += self.b2a[60 & carry << 2 | b3 >> 6] + self.b2a[63 & b3]
      ib += 1
    return s

  def binary2ascii(self, t):
    return self.bytes2ascii(self.blocks2bytes(t))

  # from http://code.activestate.com/recipes/496737/
  def xtea_encrypt(self, t0, t1, k):
    v0 = t0[0] ^ t1[0]
    v1 = t0[1] ^ t1[1]
    sum, delta, mask = 0L, 0x9e3779b9L, 0xffffffffL
    for round in range(32):
        v0 = (v0 + (((v1<<4 ^ v1>>5) + v1) ^ (sum + k[sum & 3]))) & mask
        sum = (sum + delta) & mask
        v1 = (v1 + (((v0<<4 ^ v0>>5) + v0) ^ (sum + k[sum>>11 & 3]))) & mask
    return (v0, v1)

  def encrypt(self, M):
    bd = {0: 414308958, 1: 806888581, 2: 910019038, 3: 772718910}
    bks = self.bytes2blocks(self.pad(self.str2bytes(M)))
    t0 = [1633837924, 1650680933]
    t1 = {}
    t2 = {}
    for i in xrange(0, len(bks), 2):
      t1[0] = bks[i + 0]
      t1[1] = bks[i + 1]
      t0 = self.xtea_encrypt(t0, t1, bd)
      t2[i + 0] = t0[0]
      t2[i + 1] = t0[1]
    return self.binary2ascii(t2)
