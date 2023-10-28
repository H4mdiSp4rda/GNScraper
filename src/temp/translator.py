import translators as ts

q_text = 'bonjour madame'
q_html = '''<!DOCTYPE html><html><head><title>《季姬击鸡记》</title></head><body><p>还有另一篇文章《施氏食狮史》。</p></body></html>'''

### usage
#_ = ts.preaccelerate_and_speedtest()  # Optional. Caching sessions in advance, which can help improve access speed.

#print(ts.translators_pool)
#print(ts.translate_text(q_text))
print(ts.translate_text(q_text, translator='google', from_language='auto', to_language='en'))