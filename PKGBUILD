# Maintainer: Raymond Wagenmaker <raymondwagenmaker@gmail.com>
pkgname=offlineimap-notify
pkgver=0.5.0
pkgrel=1
pkgdesc="Wrapper that adds notification sending to OfflineIMAP"
arch=(any)
url="https://bitbucket.org/raymonad/offlineimap-notify"
license=('GPL3')
depends=('offlineimap')
makedepends=('python2-distribute' 'python2-docutils')
optdepends=('python2-notify: send notifications via D-Bus')
#options=(!emptydirs)
source=("https://bitbucket.org/raymonad/offlineimap-notify/get/v$pkgver.tar.gz")
md5sums=()

package() {
  cd "$srcdir/$pkgname-$pkgver"
  python setup.py install --root="$pkgdir/" --optimize=1
  rst2man2 offlineimap-notify.rst "$pkgdir"/usr/share/man/man1/offlineimap.1
}

# vim:set ts=2 sw=2 et:
