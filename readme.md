想合并视频，但是却找不到比较好用的工具，很多都要收费，我想着「这破功能还得收费？」，于是决定自己搞一个，一开始用Python做了一个，效果还不错，完美完成了我的视频合并任务，不过没有图形界面，想分享给朋友一起用也没办法，于是昨天用Qt写了个图形界面套上去，中间还是遇到一些问题的，通过这篇文章记录一下。

## Qt
首先是Qt，要开发GUI的话（我当然要求跨平台），现在好像选择也不是很多，electron这种就算了，系统调用太麻烦，不然还是可以考虑，毕竟谁还不会点前端是吧，.Net也不考虑了，没有成熟的跨平台GUI库，Flutter的Desktop还处于Preview阶段，pass掉，数来数去也就Qt上得了台面了。于是就Qt咯。

前段时间准备面试的时候学了一下C++和Qt，正好拿来用用，不过我的视频操作库是Python的，要我C++操作ffmpeg？no，我选择PyQt，不过PyQt5现在几乎没啥中文资料，咋办嘞，之前找到一本书，少有的PyQt5教材，只不过排版很差，我看了差不多一天，给所有章节加上了书签，也熟悉了一下Python的Qt绑定，使用上和C++差不多，只不过不用自己释放对象了，很舒服，但是又由于Python动态类型，有些不熟悉的API用起来又不是那么顺手了，好在我具有多年Python经验，对着pydoc还是可以搞出来。

关于这书的下次再写一篇博客专门说好了，有些地方记录一下也不错。


软件的界面就是这样啦，用Qt Designer随便拖出来的，和VS拖控件也差不了多少。
![](https://upload-images.jianshu.io/upload_images/8869373-9ce46c92f1bde75e.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

## Python
Python语言设计得还可以，库也是真的多，我想合并视频，立刻就找到一个视频编辑库，moviepy，这个库不单可以合并视频，还可以剪切，加转场效果，调大小等多种操作，很不错，稍加利用就可以开发一个视频编辑工具了。

我来贴一下合并视频的代码：
```python
class ProcThread(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, videos: list, output_path='', parent=None):
        super(ProcThread, self).__init__(parent)
        self.videos = []
        self.output_path = output_path
        for video_file in videos:
            print(video_file)
            self.videos.append(VideoFileClip(video_file))

    def run(self) -> None:
        final_clip = concatenate_videoclips(self.videos)
        my_logger = MyBarLogger(self.message, self.progress)
        final_clip.write_videofile(self.output_path, logger=my_logger)
        self.finished.emit()
```

这里用了线程，Qt里面的线程类QThread，这样在处理视频的时候界面不会卡主，同时自己定义了几号信号，利用Qt的信号与槽的机制给GUI主线程反馈进度和完成情况。

这部分很简单啦，顺便贴一下信号和槽连接的代码（省略了一些代码）：

```python
    def start(self):
        self.thread.message.connect(self.thread_message)
        self.thread.progress.connect(self.thread_progress)
        self.thread.finished.connect(self.thread_finished)

    def thread_message(self, value):
        self.statusBar.showMessage(value)

    def thread_progress(self, value):
        self.progressBar.setValue(value)

    def thread_finished(self):
        self.btn_start.setEnabled(True)
        QMessageBox.information(self, '处理完成', '操作完成', QMessageBox.Yes)
```

这部分很简单没什么好说的，接下来说一下几个坑。

## moviepy进度展示
moviepy处理视频本来是输出在控制台的，那么进度也是在控制台输出的，但是我这写了图形界面啊，我得让他的进度输出在进度条上面才行，一开始没有思路，只好谷歌搜一下。

搜到一个github的issue，和我一样的需求，他要写GUI，需要获取处理视频的进度，定制进度条输出，如图：
![](https://upload-images.jianshu.io/upload_images/8869373-047a0bb28ed95736.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

然后我就看了下面人的回复，这个问题最早是2015年提出的，到17年还有人跟进，看来这个问题还没解决，终于最后有人提出使用proglog替换掉moviepy原本的进度库，问题终于能解决了，如图：
![](https://upload-images.jianshu.io/upload_images/8869373-4725722c99866d2c.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

然后2019年有人贴了另一个issue，本issue被开发团队关闭。

新issue是这样：
![](https://upload-images.jianshu.io/upload_images/8869373-ecf41e1ef8231832.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

就是说虽然换了proglog，但是没文档啊，这咋搞？我看了一眼，这个proglog确实文档很少，有点坑。

不过下面还是有人贴了地址，是proglog项目的地址，点进去看看。
[https://github.com/Edinburgh-Genome-Foundry/Proglog](https://github.com/Edinburgh-Genome-Foundry/Proglog)

嗯，找到自定义回调函数的地方了：
![](https://upload-images.jianshu.io/upload_images/8869373-884047d6791563b8.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

看来按这个写就好了，但是坑人啊，我试了一下，这样只会输出message，就是说进行到哪一步了，没输出进度啊，这作者坑人。

但是进度明明是有的，于是只能调试程序的时候打断点跟踪了，过程我就不放了，反正打断点的时候发现，ProgressBarLogger类有个state属性，看介绍是这样：
>Instance attribute state of proglog.proglog.ProgressLogger

看了一下里面的内容，有个bars字段，拿出来看，是个OrderedDict对象，之前我没接触过这个数据结构，有点懵，其实它就是个排好序的dict，要遍历着实费劲，搞了半天（也有可能是熬夜写代码头脑不灵活）才弄好。

moviepy更新进度的时候，就是在这个state["bars"]里面传，一个任务一个dict，这个dict里面包含title、index、total等字段，total就是工作量了，index就是现在进行到哪，到这问题就OK啦，我拿index和total一除再乘以100不就是百分比了吗？这不就完事了，然后我再把线程的信号一传，实时显示进度，完美~！

贴一下代码：
```python
class MyBarLogger(ProgressBarLogger):
    actions_list = []

    def __init__(self, message, progress):
        self.message = message
        self.progress = progress
        super(MyBarLogger, self).__init__()

    def callback(self, **changes):
        bars = self.state.get('bars')
        index = len(bars.values()) - 1
        if index > -1:
            bar = list(bars.values())[index]
            progress = int(bar['index'] / bar['total'] * 100)
            self.progress.emit(progress)
        if 'message' in changes: self.message.emit(changes['message'])
```

## pyinstaller打包
本来没什么好说的，但是打包完也太大了吧，600+m，这谁顶得住，而且打包过程还出错。
第一次出错是：
>RecursionError: maximum recursion depth exceeded

就是超出python的最大递归深度，这没办法，可能包太多了，目录太深入，解决办法是调整递归深度上限。

执行 pyinstaller，会生成 filename.spec文件，在这个 filename.spec 文件开头添加代码，把递归深度调到10w：
```python
import sys
sys.setrecursionlimit(100000)
```

解决了问题，然后第二个问题来了，由于我代码里面用了中文，但是Windows的cmd默认不是utf-8的，报了这个错：
>UnicodeDecodeError: 'utf-8' codec can't decode byte 0xce in position 130: invalid continuation b

解决方法是：
1. 换Linux（误）
2. 改变控制台编码（临时）：使用命令 chcp 65001

这样就完成了。

还有一点，单文件打包出来600多m，太大了无法运行，所以还是不要打包单文件的，这样大小虽然有1G多，但是用7z压缩一下就200多m，还可以接受，hhh。


## 总结
PyQt勉强可以开发吧，和C#这些那没得比，但是跨平台还是不错的，就是打包之后太大了。

相关代码已经开源：[https://github.com/Deali-Axy/VideoMerge](https://github.com/Deali-Axy/VideoMerge)


