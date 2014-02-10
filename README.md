
#### To give user-mode access to port 80:

 iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080

### Exclusions

Each HIT may specify a set of exclusions, a whitespace separated list of other HIT IDs such that if a worker has completed any of the HITs listed as exclusions she may not complete the HIT that listed those exlclusions. Perhaps an example would be most informative. Consider the following HITs:

```xml
  <hits>
    <hit>
      <hitid>1</hitid>
      <exclusions>2</exclusions>
      <tasks>
	1
	2
      </tasks>
    </hit>
    <hit>
      <hitid>2</hitid>
      <tasks>
	1
      </tasks>
    </hit> 
  </hits>
```

In this case, a worker who first completes HIT 2 may not then complete HIT 1, since HIT 1 excludes HIT 2. However, since HIT 2 lists no exclusions, a worker who first completes HIT 1 would then be permitted to complete HIT 2. There is no enforcement that exclusions be symmetric.


### Scale Questions

After the scale question type was dropped from a previous release, scale questions must now be added as categorical types. All questions may have an options tag, and the nested layout tag specifies whether the radio buttons are rendered horizontally or vertically (the latter being the default). Several other options are available, as in the following example:

```xml
<options>
  <layout>horizontal</layout>
  <lowLabel>Conservative</lowLabel>
  <highLabel>Liberal</highLabel>
  <outsideCategories>N/A</outsideCategories>
  <outsideCategories>Unsure</outsideCategories>
</options>
```

This will yield the following layout:

![new project](https://github.com/sgrondahl/news_crowdsourcer/raw/master/markdown/ScaleQuestion.PNG)


### Nested Categorical Questions

See src/tests/test_xml_cat_expand_1.xml for example usage. To control nesting, encode nests in text tags, i.e. 

```xml
<text> Hard News | Science and Tech | Computers </text>.
```

The <value> will be sent along if the rightmost category is selected. It is possible to have asymmetric trees, so in addition to the above you could add 

```xml
<text> Hard News | Politics </text>.
```

Then if the user selects Hard News > Politics, no more expansion will happen and the question will be complete. Technically it is also possible to have optional specificity, i.e. add a category with 

```xml
<text> Hard News | Politics | National </text>
```

This would allow selection of either HN > Politics or HN > Politics > National, and both would be acceptable. In this case the final expansion will occur to show "National", but technically the user could continue without selecting it and not receive an error.


### Full Example

A full XML configuration file that demonstrates all of the various features follows:

```xml
<xml>
  <modules>
    <module>
      <header>Questions on Demographics</header>
      <name>demographics</name>
      <questions>
	<question>
	  <helptext>This is your age in years.</helptext>
	  <varname>age</varname>
	  <questiontext>What is your age?</questiontext>
	  <valuetype>numeric</valuetype>
	</question>
	<question>
	  <helptext>We want to better understand the strenghts and weaknesses of our survey in order to improve it for future workers. Your answer to this question will not influence your payment.</helptext>
	  <varname>thoughts</varname>
	  <questiontext>What were your overall perceptions of the survey? Which questions were most confusing? You may also submit any other comments that you may have.</questiontext>
	  <valuetype>text</valuetype>
	</question>
	<question>
	  <varname>married</varname>
	  <questiontext>Are you married?</questiontext>
	  <helptext>You might feel that this is a vague question. Thankfully, we've added helptext to clear things up. Here you go: You'll receive notifications for all issues, pull requests, and comments that happen inside the repository. If you would like to stop watching this repository, you can manage your settings somewhere.</helptext>
	  <valuetype>categorical</valuetype>
	  <content>
	    <categories>
	      <category>
		<text>Yes</text>
		<value>yes</value>
	      </category>
	      <category>
		<text>No</text>
		<value>no</value>
	      </category>
	    </categories>
	  </content>
	</question>
	<question>
	  <varname>bias</varname>
	  <questiontext>How biased is this?</questiontext>
	  <valuetype>categorical</valuetype>
	  <options>
	    <layout>horizontal</layout>
	    <lowLabel>Conservative</lowLabel>
	    <highLabel>Liberal</highLabel>
	    <outsideCategories>N/A</outsideCategories>
	    <outsideCategories>Unsure</outsideCategories>
	  </options>
	  <content>
	    <categories>
	      <category>
		<text>1</text>
		<value>1</value>
	      </category>
	      <category>
		<text>2</text>
		<value>2</value>
	      </category>
	      <category>
		<text>3</text>
		<value>3</value>
	      </category>
	      <category>
		<text>4</text>
		<value>4</value>
	      </category>
	      <category>
		<text>5</text>
		<value>5</value>
	      </category>
	      <category>
		<text>6</text>
		<value>6</value>
	      </category>
	    </categories>
	  </content>
	</question>
	<question>
	  <varname>level_category</varname>
	  <questiontext>What is this category?</questiontext>
	  <valuetype>categorical</valuetype>
	  <content>
	    <categories>
	      <category>
		<text>Hard|Science|Interesting</text>
		<value>hard_science_interesting</value>
	      </category>
	      <category>
		<text>Hard|Law</text>
		<value>hard_law</value>
	      </category>
	      <category>
		<text>Hard|Science|Difficult</text>
		<value>hard_science_difficult</value>
	      </category>
	      <category>
		<text>Hard|Science|Boring</text>
		<value>hard_science_boring</value>
	      </category>
	      <category>
		<text>Soft|Animals</text>
		<value>soft</value>
	      </category>
	    </categories>
	  </content>
	</question>
      </questions>
    </module>
  </modules>
  <tasks>
    <task>
      <content>content1.html</content>
      <taskid>1</taskid>
      <modules>demographics</modules>
    </task>
    <task>
      <content>content2.html</content>
      <taskid>2</taskid>
      <modules>demographics</modules>
    </task>
  </tasks>
  <hits>
    <hit>
      <hitid>1</hitid>
      <exclusions>2</exclusions>
      <tasks>
	1
	2
      </tasks>
    </hit>
    <hit>
      <hitid>2</hitid>
      <exclusions>1 3</exclusions>
      <tasks>
	1
      </tasks>
    </hit> 
    <hit>
      <hitid>3</hitid>
      <exclusions>1</exclusions>
      <tasks>
	2
      </tasks>
    </hit>
 </hits>
  <documents>
    <document>
      <name>content1.html</name>
      <content>This is stuff for content1.</content>
    </document>
  </documents>
</xml>
```