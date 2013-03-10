# Maintainer: Raymond Wagenmaker <raymondwagenmaker@gmail.com>
pkgname=offlineimap-notify
pkgver=0.5.0
pkgrel=1
pkgdesc="Wrapper that adds notification sending to OfflineIMAP"
arch=(any)
url="https://bitbucket.org/raymonad/offlineimap-notify"
license=('GPL3')
depends=('offlineimap' 'python2-distribute')
makedepends=('python2-docutils')
optdepends=('python2-notify: send notifications via D-Bus')
#options=(!emptydirs)
#source=("https://bitbucket.org/raymonad/offlineimap-notify/get/v$pkgver.tar.gz")
source=("https://bitbucket.org/raymonad/offlineimap-notify/get/master.tar.gz")
md5sums=('dc8f70c21ae645b9d747cfecdea57013')

package() {
  #cd "$srcdir/$pkgname-$pkgver"
  cd $srcdir/raymonad*
  python2 setup.py install --root="$pkgdir/" --optimize=1
  rst2man2 offlineimap-notify.rst offlineimap.1
  install -Dm644 offlineimap.1 "$pkgdir"/usr/share/man/man1/offlineimap.1
}

# vim:set ts=2 sw=2 et:
