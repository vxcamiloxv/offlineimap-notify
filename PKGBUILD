# Maintainer: Raymond Wagenmaker <raymondwagenmaker@gmail.com>
pkgname=offlineimap-notify
pkgver=0.5.0
_taghash= # Bitbucket tarballs have silly names
pkgrel=2
pkgdesc="Wrapper that adds notification sending to OfflineIMAP"
arch=(any)
url="https://bitbucket.org/raymonad/offlineimap-notify"
license=('GPL3')
depends=('offlineimap' 'python2-distribute')
makedepends=('python2-docutils')
optdepends=('python2-notify: send notifications via D-Bus')
source=("https://bitbucket.org/raymonad/$pkgname/get/v$pkgver.tar.gz")

build() {
  cd "$srcdir/raymonad-$pkgname-$_taghash"
  rst2man2 offlineimap-notify.rst offlineimap-notify.1
}

package() {
  cd "$srcdir/raymonad-$pkgname-$_taghash"
  python2 setup.py install --root="$pkgdir/" --optimize=1
  install -Dm644 offlineimap-notify.1 "$pkgdir"/usr/share/man/man1/offlineimap-notify.1
}

# vim:set ts=2 sw=2 et:
